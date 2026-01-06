def mail_input_element_strategies(email):
    return [
        # Strategy 1: Standard email input
        {
            "name": "standard email input",
            "sendKey": {
                "rootTag": "input",
                "attributes": {"type": "email"},
                "contentInput": email,
                "typeSendKey": "human",
                "timeDelayAction": 1,
                "timeout": 10,
            }
        },
        # Strategy 2: Try with id attribute
        {
            "name": "email input by id",
            "sendKey": {
                "rootTag": "input",
                "attributes": {"id": "identifierId"},
                "contentInput": email,
                "typeSendKey": "human",
                "timeDelayAction": 1,
                "timeout": 10,
            }
        },
        # Strategy 3: Try with name attribute
        {
            "name": "email input by name",
            "sendKey": {
                "rootTag": "input",
                "attributes": {"name": "identifier"},
                "contentInput": email,
                "typeSendKey": "human",
                "timeDelayAction": 1,
                "timeout": 10,
            }
        },
    ]


def next_button_strategies():
    return [

        # Strategy 4: Button with span containing "Tiếp theo" (Vietnamese)
        {
            "parentTag": "button",
            "rootTag": "span",
            "text": "Tiếp theo",
            "timeout": 5,
            'numberActionFakePerson': 3,
            'scrollToElement': 'vertical',
        },
        # Strategy 1: Use button ID (most reliable)
        {
            "rootTag": "button",
            "attributes": {"id": "identifierNext"},
            "timeout": 5,
            'isGoOnTop': True,
            'numberActionFakePerson': 3,
            'scrollToElement': 'vertical',
        },

        # Strategy 3: Button with span containing "Next" (English)
        {
            "parentTag": "button",
            "rootTag": "span",
            "text": "Next",
            "timeout": 5,
            'numberActionFakePerson': 3,
            'scrollToElement': 'vertical',
        },
        # Strategy 5: Direct button with "Next" text
        {
            "rootTag": "button",
            "text": "Next",
            "timeout": 5,
            'numberActionFakePerson': 3,
            'scrollToElement': 'vertical',
        },
        # Strategy 6: Direct button with "Tiếp theo" text
        {
            "rootTag": "button",
            "text": "Tiếp theo",
            "timeout": 5,
            'numberActionFakePerson': 3,
            'scrollToElement': 'vertical',
        },
        # Strategy 7: Div with role="button" containing "Next"
        {
            "rootTag": "div",
            "attributes": {"role": "button"},
            "text": "Next",
            "timeout": 5,
            'numberActionFakePerson': 3,
            'scrollToElement': 'vertical',
        },
        # Strategy 8: Div with role="button" containing "Tiếp theo"
        {
            "rootTag": "div",
            "attributes": {"role": "button"},
            "text": "Tiếp theo",
            "timeout": 5,
            'numberActionFakePerson': 3,
            'scrollToElement': 'vertical',
        },
    ]


def list_msgs_email_not_valid():
    error_messages = [
        "Enter a valid email or phone number",
        "Nhập tên, email hoặc số điện thoại"
    ]
    return error_messages


def list_msgs_pw_not_valid():
    return [
        "Wrong password",
        'Mật khẩu không chính xác',
    ]


def challenge_selection_strategies():
    """
    Strategies to select the email verification challenge method.
    Works for both English and Vietnamese pages.
    Returns a list of strategy dictionaries compatible with UtilActions.click()
    """
    return [
        {
            'rootTag': 'div',
            'attributes': {
                'role': 'link'
            },
            'text': 'Google Authenticator',  # English
            'isContains': True,
            'timeout': 5,
            'scrollToElement': 'vertical'
        },
        {
            'rootTag': 'div',
            'attributes': {
                'data-challengetype': '30',
                'data-action': 'selectchallenge'
            },
            'timeout': 5,
            'scrollToElement': 'vertical'
        },
        {
            'rootTag': 'div',
            'attributes': {
                'data-challengeid': '3'
            },
            'timeout': 5,
            'scrollToElement': 'vertical'
        },
        {
            'rootTag': 'div',
            'attributes': {
                'jsname': 'EBHGs',
                'data-challengetype': '30'
            },
            'timeout': 5,
            'scrollToElement': 'vertical'
        },
        {
            'rootTag': 'div',
            'attributes': {
                'role': 'link'
            },
            'text': '@gmail.com',
            'isContains': True,
            'timeout': 5,
            'scrollToElement': 'vertical'
        },
        {
            'rootTag': 'div',
            'attributes': {
                'role': 'link'
            },
            'text': 'verification code',  # English
            'isContains': True,
            'timeout': 5,
            'scrollToElement': 'vertical'
        },
        {
            'rootTag': 'div',
            'attributes': {
                'role': 'link'
            },
            'text': 'mã xác minh',  # Vietnamese
            'isContains': True,
            'timeout': 5,
            'scrollToElement': 'vertical'
        },
        {
            'rootTag': 'div',
            'attributes': {
                'role': 'link',
                'data-action': 'selectchallenge'
            },
            'timeout': 5,
            'typeFind': 'one',
            'scrollToElement': 'vertical'
        },
        {
            'rootTag': 'div',
            'attributes': {
                'role': 'link',
                'tabindex': '0',
                'jsname': 'EBHGs'
            },
            'timeout': 5,
            'typeFind': 'one',
            'scrollToElement': 'vertical'
        }
    ]


def two_fa_check_strategies():
    return [
        {"rootTag": "input", "attributes": {"aria-label": "Nhập mã"}},
        {"rootTag": "input", "attributes": {"id": "totpPin"}},
        {"rootTag": "input", "attributes": {"name": "totpPin"}},
        {"rootTag": "input", "attributes": {"type": "tel"}},
        {"rootTag": "input", "attributes": {"aria-label": "Enter code"}},
    ]


def two_fa_input_strategies(code2faDecode):
    return [
        # Strategy 1: Use input ID (most reliable)
        {
            "rootTag": "input",
            "attributes": {"id": "totpPin"},
            "contentInput": code2faDecode,
            "typeSendKey": "human",
            "isRemove": True,
            "timeDelayAction": 1,
            "timeout": 5,
        },
        # Strategy 2: Use matching name
        {
            "rootTag": "input",
            "attributes": {"name": "totpPin"},
            "contentInput": code2faDecode,
            "typeSendKey": "human",
            "isRemove": True,
            "timeDelayAction": 1,
            "timeout": 5,
        },
        # Strategy 3: Type tel (generic)
        {
            "rootTag": "input",
            "attributes": {"type": "tel"},
            "contentInput": code2faDecode,
            "typeSendKey": "human",
            "isRemove": True,
            "timeDelayAction": 1,
            "timeout": 5,
        },
    ]
