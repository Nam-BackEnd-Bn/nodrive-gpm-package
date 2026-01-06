from loguru import logger

from nodrive_gpm_package.services.gmail_service.gmail_helper import list_msgs_email_not_valid, next_button_strategies, \
    mail_input_element_strategies


class InputMailService:
    def __init__(self, tab, email):
        self.tab = tab
        self.email = email

    async def _check_input_email(self):
        try:
            from nodrive_gpm_package.utils import UtilActions
            await UtilActions.getElement(
                tab=self.tab,
                rootTag="input",
                attributes={"type": "email"},
                timeout=3,
            )
            return True
        except:
            logger.info("INPUT_EMAIL_NOT_FOUND_TO_LOGIN_GMAIL")
            return False

    async def _check_click_next_success(self, next_strategy, strategy):
        from nodrive_gpm_package.utils import UtilActions
        try:
            await UtilActions.click(tab=self.tab, **next_strategy)
            logger.info(f"✅ Successfully clicked Next button using {strategy['name']}")
            return True
        except Exception as e:
            logger.debug(f"Next button click strategy failed: {e}")
            return False

    async def _try_fill_email(self, strategy):
        try:
            import asyncio
            from nodrive_gpm_package.utils import UtilActions
            logger.info(f"Trying {strategy['name']}...")
            await UtilActions.sendKey(
                tab=self.tab,
                **strategy["sendKey"]
            )

            await asyncio.sleep(1)
            return True
        except Exception as e:
            logger.debug(f"Trying {strategy['name']} NOT_WORKING_TO_FILL_EMAIL")
            return False

    async def _check_email_is_not_valid(self):
        from nodrive_gpm_package.utils import UtilActions
        for error_msg in list_msgs_email_not_valid():
            try:
                await UtilActions.getElement(
                    tab=self.tab,
                    text=error_msg,
                    timeout=3,
                )
                logger.error(f"Invalid email or phone number detected: {error_msg}")
                return True
            except (IndexError, Exception):
                return False

    async def _fill_input_email(self, strategies):
        for strategy in strategies:
            try:
                if not await self._try_fill_email(strategy):
                    continue

                for next_strategy in next_button_strategies():
                    if await self._check_click_next_success(next_strategy, strategy):
                        break

                if await self._check_email_is_not_valid():
                    break

                logger.info(f"Email input succeeded but Next button not found for {strategy['name']}")
                return True
            except Exception as e:
                logger.debug(f"Strategy {strategy['name']} failed: {e}")
                continue

        return False

    async def set_input_email(
            self,
    ):
        if not await self._check_input_email():
            return False

        strategies = mail_input_element_strategies(self.email)

        return await self._fill_input_email(strategies)
