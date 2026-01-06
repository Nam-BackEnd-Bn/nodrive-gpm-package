from nodrive_gpm_package.services.gmail_service.account_service import AccountService
from nodrive_gpm_package.services.gmail_service.input_2fa_service import InputTwoFAService
from nodrive_gpm_package.services.gmail_service.input_mail_service import InputMailService
from nodrive_gpm_package.services.gmail_service.input_password_service import InputPasswordService


class GmailService:
    def __init__(self, tab, email):
        self.tab = tab
        self.email = email

        self.account_service = AccountService(tab, email['email'])
        self.input_mail_service = InputMailService(tab, email['email'])
        self.input_password_service = InputPasswordService(tab, email['password'])
        self.input_2fa_service = InputTwoFAService(tab, email['code2FA'])

    async def login_gmail(self) -> bool:
        if await self.account_service.check_and_click_existing_account():
            return True

        if not await self.input_mail_service.set_input_email():
            return False

        if not await self.input_password_service.set_input_password():
            return False

        if not await self.input_2fa_service.set_input_code():
            return False

        return True
