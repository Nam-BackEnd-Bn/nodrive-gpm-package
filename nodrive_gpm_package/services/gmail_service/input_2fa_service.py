import asyncio

from loguru import logger

from nodrive_gpm_package.services.gmail_service.gmail_helper import challenge_selection_strategies, \
    two_fa_check_strategies, next_button_strategies, two_fa_input_strategies


class InputTwoFAService:
    def __init__(self, tab, code):
        self.tab = tab
        self.code = code

    async def _select_challenge_method(self):
        from nodrive_gpm_package.utils import UtilActions
        strategies = challenge_selection_strategies()

        logger.info("Checking for verification challenge options...")

        # First, let's verify we're on the right page
        try:
            page_content = await self.tab.get_content()
            if 'Choose how you want to sign in' in page_content or 'Chọn cách bạn muốn đăng nhập' in page_content:
                logger.info("✅ Challenge selection page detected")
            else:
                logger.warning("⚠️ May not be on challenge selection page")
        except Exception as e:
            logger.warning(f"Could not verify page content: {e}")

        for idx, strategy in enumerate(strategies, 1):
            try:
                logger.info(f"Trying strategy {idx}/{len(strategies)}")
                await UtilActions.click(tab=self.tab, **strategy)
                logger.info(f"✅ Selected challenge method:")
                await asyncio.sleep(1)  # Wait for navigation/update
                return True
            except Exception as e:
                logger.debug(f"Strategy failed: {str(e)}")
                continue

        logger.warning("⚠️ No challenge selection needed or none found.")
        return False

    async def _check_has_input_2fa(self):
        try:
            from nodrive_gpm_package.utils import UtilActions
            # Try to find any common 2FA input field
            input_strategies = two_fa_check_strategies()

            for strategy in input_strategies:
                try:
                    await UtilActions.getElement(
                        tab=self.tab,
                        timeout=2,
                        **strategy
                    )
                    return True
                except:
                    continue

            logger.info("INPUT_CODE_2FA_NOT_FOUND")
            return False
        except Exception as e:
            logger.error(f"Error checking input code: {e}")
            return False

    async def _gen_2fa_code(self):
        from nodrive_gpm_package.utils import UtilDecode

        try:
            # Generate TOTP
            code2faDecode = UtilDecode.code2Fa(self.code)
            logger.info(f"Generated 2FA code: {code2faDecode}")
            return code2faDecode
        except Exception as e:
            logger.error(f"Error decoding 2FA secret: {e}")

    async def _click_next_final(self):
        from nodrive_gpm_package.utils import UtilActions
        used_strategy = None
        for next_strategy in next_button_strategies():
            try:
                await UtilActions.click(tab=self.tab, **next_strategy)
                logger.info(f"✅ Clicked Next after 2FA")
                used_strategy = next_strategy
                return True
            except Exception:
                continue

        await asyncio.sleep(3)

    async def _check_2fa_is_valid(self):
        from nodrive_gpm_package.utils import UtilActions
        logger.info("Checking if 2FA code was accepted...")
        wrong_code_found = False
        wrong_code_messages = ["Wrong code", "Mã không đúng", "Sai mã"]
        for wrong_msg in wrong_code_messages:
            try:
                await UtilActions.getElement(
                    tab=self.tab,
                    text=wrong_msg,
                    timeout=3,
                    timeDelay=1,
                )
                wrong_code_found = True
                logger.warning(f"Wrong 2FA code message found: {wrong_msg}")
                break
            except (IndexError, Exception):
                continue

        if wrong_code_found:
            # TODO: Update status Wrong 2FA to Database
            logger.error('2FA incorrect')
            return False
        return True

    async def _fill_input_code(self):
        if not self.code:
            logger.error("No 2FA code provided!")
            return False

        code2fa = await self._gen_2fa_code()

        from nodrive_gpm_package.utils import UtilActions
        input_success = False
        for strategy in two_fa_input_strategies(code2fa):
            try:
                await UtilActions.sendKey(tab=self.tab, **strategy)
                input_success = True
                break
            except Exception:
                continue

        if not input_success:
            logger.error("Failed to input 2FA code with all strategies")
            return False

        return True

    async def set_input_code(self):
        # 1. Try to select a challenge method if we are on that screen
        if not self._check_has_input_2fa():
            await self._select_challenge_method()

        # 2. Check if the input field is available
        if not await self._check_has_input_2fa():
            # Retry checking again after a short delay in case selection just happened
            await asyncio.sleep(2)
            if not await self._check_has_input_2fa():
                raise Exception('ERROR_2FA_FIELD_NOT_FOUND')

        # 3. Input the code
        await self._fill_input_code()

        # Click Next
        await self._click_next_final()

        # 4. Check 2fa Valid
        return await self._check_2fa_is_valid()
