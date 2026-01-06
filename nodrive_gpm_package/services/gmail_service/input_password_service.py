from loguru import logger

from nodrive_gpm_package.services.gmail_service.gmail_helper import list_msgs_pw_not_valid


class InputPasswordService:
    def __init__(self, tab, password):
        self.tab = tab
        self.password = password

    async def _check_input_password(self):
        try:
            from nodrive_gpm_package.utils import UtilActions
            await UtilActions.getElement(
                tab=self.tab,
                rootTag="input",
                attributes={"type": "password"},
                timeout=3,
            )
            return True
        except:
            logger.info("INPUT_PASSWORD_NOT_FOUND_TO_LOGIN_GMAIL")
            return False

    async def _check_click_next_success(self, next_strategy):
        from nodrive_gpm_package.utils import UtilActions
        try:
            await UtilActions.click(tab=self.tab, **next_strategy)
            logger.info(f"✅ Successfully clicked Next button ")
            return True
        except Exception as e:
            logger.debug(f"Next button click strategy failed: {e}")
            return False

    async def _try_fill_password(self):
        try:
            import asyncio
            from nodrive_gpm_package.utils import UtilActions
            await UtilActions.sendKey(
                tab=self.tab,
                rootTag="input",
                attributes={
                    "type": "password",
                },
                contentInput=self.password,
                typeSendKey="human",
            )

            await asyncio.sleep(1)
            return True
        except Exception as e:
            logger.debug(f"TRY_FILL_PASSWORD_NOT_WORKING")
            return False

    async def _check_password_is_not_valid(self):
        from nodrive_gpm_package.utils import UtilActions
        for error_msg in list_msgs_pw_not_valid():
            try:
                await UtilActions.getElement(
                    tab=self.tab,
                    text=error_msg,
                    timeout=3,
                )
                logger.error(f"Invalid password detected: {error_msg}")
                return True
            except (IndexError, Exception):
                return False

    async def _fill_input_password(self):
        if not await self._try_fill_password():
            return False

        for next_strategy in next_button_strategies():
            if await self._check_click_next_success(next_strategy):
                break

        if await self._check_password_is_not_valid():
            return False

        logger.info(f"Password input succeeded but Next button not found")
        return True

    async def set_input_password(self):
        if not await self._check_input_password():
            return False

        return await self._fill_input_password()
