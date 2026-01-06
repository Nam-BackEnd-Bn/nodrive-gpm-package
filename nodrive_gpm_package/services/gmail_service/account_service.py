from loguru import logger


class AccountService:
    def __init__(self, tab, email):
        self.tab = tab
        self.email = email

    async def check_and_click_existing_account(self):
        logger.info(f"Checking if account {self.email} is already available...")

        from nodrive_gpm_package.utils import UtilActions
        try:
            await UtilActions.click(
                tab=self.tab,
                parentTag="div",
                parentAttributes={
                    "role": "link"
                },
                rootTag="div",
                text=self.email,
                timeout=5,
            )
            logger.info(f"Found and clicked existing account: {self.email}")
            return True
        except (IndexError, Exception) as e:
            logger.debug(f"Account not found on page (will proceed with email input): {e}")
            return False
