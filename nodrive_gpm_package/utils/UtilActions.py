import asyncio, time, random, nodriver as nd, re
from typing import Literal, Dict, List, Union
try:
    import win32api
    import win32con
except ImportError:
    win32api = None
    win32con = None
from . import UtilActionsBrowser, UtilUserAgent

"""
Utility functions for nodriver automation, adapted from Selenium-based utilities.
These functions extend the nodrive_gpm_package.utils.UtilActions functionality.

To use these functions in the nodrive_gpm_package, add them to:
nodrive_gpm_package/utils/__init__.py or nodrive_gpm_package/utils/util_actions.py

These are adapted versions that work with nodriver instead of Selenium.
"""
import asyncio
import random
import time
from typing import Literal, Optional
from loguru import logger
import nodriver as nd


ElementsTag = Literal[
    "textarea",
    "header",
    "button",
    "time",
    "a",
    "span",
    "div",
    "p",
    "strong",
    "i",
    "ul",
    "ol",
    "li",
    "nav",
    "svg",
    "use",
    "img",
    "input",
    "body",
    "head",
    "audio",
    "pre",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
]

AttributesTag = Literal["text", "class", "id", "role", "type", "aria-label"]


def buildSelector(
    rootTag: str,
    attributes: dict = None,
    parentAttributes: dict = None,
    parentTag: str = None,
) -> str:
    """
    Build CSS selector from tag and attributes

    Args:
        rootTag (str): Main HTML tag to find (e.g., 'div', 'span').
        attributes (dict): Dictionary containing attributes of the main tag (e.g., {'class': 'example'}).
        parentAttributes (dict, optional): Dictionary containing attributes of parent tag (if any). Default is None.
        isContains (bool, optional): Determines whether to use contains() for text attribute. Default is True.
        parentTag (str, optional): HTML tag of parent element (if any). Default is None.

    Returns:
        str: CSS selector string
    """

    if rootTag is None:
        return None

    def buildConditions(attrs: dict, tag: str) -> str:
        if not attrs:
            return tag

        selector_parts = [tag]

        for key, val in attrs.items():
            if val == "":
                # Attribute exists
                selector_parts.append(f"[{key}]")
            elif key == "class":
                # Multiple classes
                classes = val.split()
                for cls in classes:
                    selector_parts.append(f".{cls.strip()}")
            elif key == "id":
                # ID selector
                selector_parts.append(f"#{val}")
            else:
                # Regular attribute with value
                selector_parts.append(f'[{key}="{val}"]')

        return "".join(selector_parts)

    rootSelector = buildConditions(attributes, rootTag)

    if parentTag and parentAttributes:
        parentSelector = buildConditions(parentAttributes, parentTag)
        selector = f"{parentSelector} {rootSelector}"
    else:
        selector = rootSelector

    return selector


def buildXpath(
    rootTag: str,
    text=None,
    attributes: dict = None,
    parentAttributes: dict = None,
    isContains: bool = True,
    parentTag: str = None,
) -> str:
    """
    Args:
        rootTag (str): Thẻ HTML chính (root tag) cần tìm (ví dụ: 'div', 'span').
        text (str, optional): Text content cần tìm trong thẻ.
        attributes (dict): Từ điển chứa các thuộc tính của thẻ chính (ví dụ: {'class': 'example'}).
        parentAttributes (dict, optional): Từ điển chứa các thuộc tính của thẻ cha (nếu có). Mặc định là None.
        isContains (bool, optional): Xác định xem có sử dụng contains() trong XPath cho thuộc tính text không. Mặc định là True.
        parentTag (str, optional): Thẻ HTML của thẻ cha (nếu có). Mặc định là None.
    """

    def buildConditions(attrs: dict) -> str:
        if not attrs:
            return ""

        conditions_list = []
        for key, val in attrs.items():
            if val == "":
                condition = f"@{key}"
            elif key == "class":
                condition = " and ".join(
                    f"contains(@class, '{cls.strip()}')" for cls in val.split()
                )
            elif key == "aria-label":
                if isContains:
                    condition = f"contains(@{key}, '{val}')"
                else:
                    condition = f"@{key}='{val}'"
            else:
                condition = f"@{key}='{val}'"

            conditions_list.append(condition)

        return f"[{' and '.join(conditions_list)}]" if conditions_list else ""

    # Build conditions for attributes
    rootConditions = buildConditions(attributes)
    parentConditions = buildConditions(parentAttributes) if parentAttributes else ""

    # Handle text parameter separately
    if text:
        strCharacter = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if isContains:
            # Chuyển cả hai bên về lowercase để so sánh không phân biệt hoa thường
            text_condition = f"contains(translate(normalize-space(.), '{strCharacter}', '{strCharacter.lower()}'), '{text.strip().lower()}')"
        else:
            text_condition = f"translate(normalize-space(.), '{strCharacter}', '{strCharacter.lower()}') = '{text.strip().lower()}'"

        # Add text condition to root conditions
        if rootConditions:
            rootConditions = rootConditions[:-1] + f" and {text_condition}]"
        else:
            rootConditions = f"[{text_condition}]"

    if parentTag:
        xpath = f"//*[local-name()='{parentTag}']{parentConditions}//*[local-name()='{rootTag}']{rootConditions}"
    else:
        xpath = f"//*[local-name()='{rootTag}']{rootConditions}"

    return xpath


def buildChildrenSelector(
    childrenTag: str,
    childrenAttributes: dict,
) -> str:
    """
    Build CSS selector for children elements relative to parent

    Args:
        childrenTag (str): HTML tag of children element
        childrenAttributes (dict): Attributes of children element
        isContains (bool): Use contains() for text attribute

    Returns:
        str: CSS selector string
    """

    def buildConditions(attrs: dict, tag: str) -> str:
        if not attrs:
            return tag

        selector_parts = [tag]

        for key, val in attrs.items():
            if val == "":
                # Attribute exists
                selector_parts.append(f"[{key}]")
            elif key == "class":
                # Multiple classes
                classes = val.split()
                for cls in classes:
                    selector_parts.append(f".{cls.strip()}")
            elif key == "id":
                # ID selector
                selector_parts.append(f"#{val}")
            else:
                # Regular attribute with value
                selector_parts.append(f'[{key}="{val}"]')

        return "".join(selector_parts)

    childrenSelector = buildConditions(childrenAttributes, childrenTag)
    return childrenSelector


async def humanLikeMouseMovement(
    tab: nd.Tab, min_movements: int = 1, max_movements: int = 3
) -> bool:
    """
    Simulate more human-like mouse movements with pauses and micro-movements
    """
    try:
        # Get current mouse position (if possible) or start from center
        viewport = await tab.evaluate(
            "() => ({width: window.innerWidth, height: window.innerHeight})"
        )

        if not viewport:
            viewport = {"width": 1920, "height": 1080}

        current_x = viewport["width"] // 2
        current_y = viewport["height"] // 2

        # Perform 5-8 human-like movements
        num_movements = random.randint(min_movements, max_movements)

        for _ in range(num_movements):
            # Small random movements (like real human fidgeting)
            dx = random.randint(-100, 100)
            dy = random.randint(-100, 100)

            new_x = max(50, min(viewport["width"] - 50, current_x + dx))
            new_y = max(50, min(viewport["height"] - 50, current_y + dy))

            # Move in small steps to simulate smooth movement
            steps = random.randint(3, 7)
            step_x = (new_x - current_x) / steps
            step_y = (new_y - current_y) / steps

            for step in range(steps):
                intermediate_x = int(current_x + step_x * step)
                intermediate_y = int(current_y + step_y * step)

                try:
                    if hasattr(tab, "mouse_move"):
                        await tab.mouse_move(intermediate_x, intermediate_y)
                    else:
                        await tab.send(
                            "Input.dispatchMouseEvent",
                            {
                                "type": "mouseMoved",
                                "x": intermediate_x,
                                "y": intermediate_y,
                            },
                        )

                    # Very short delay between micro-movements
                    await asyncio.sleep(random.uniform(0.01, 0.03))

                except Exception as e:
                    print(f"Micro-movement error: {e}")

            current_x, current_y = new_x, new_y

            # Pause like human thinking
            await asyncio.sleep(random.uniform(0.2, 0.5))

        return True

    except Exception as e:
        print(f"❌ Error in human-like mouse movement: {e}")
        return False


async def getElement(
    tab: nd.Tab,
    rootTag: ElementsTag = None,
    attributes: Dict[AttributesTag, str] = None,
    parentAttributes: Dict[AttributesTag, str] = None,
    parentTag: ElementsTag = None,
    text: str = None,
    isContains: bool = True,
    timeout: float = 30,
    timeDelay: float = 1,
    typeFind: Literal["one", "multi"] = "one",
    isGoOnTop: bool = True,
) -> Union[nd.Element, List[nd.Element], None]:
    """
    Get element(s) based on tag and attributes
    """
    if timeDelay > 0:
        await asyncio.sleep(timeDelay)

    xpath = None
    selector = None
    if text or rootTag:
        xpath = buildXpath(
            text=text,
            rootTag=rootTag,
            attributes=attributes,
            parentAttributes=parentAttributes,
            parentTag=parentTag,
            isContains=isContains,
        )
    else:
        selector = buildSelector(
            rootTag=rootTag,
            attributes=attributes,
            parentAttributes=parentAttributes,
            parentTag=parentTag,
        )

    print(
        f"\nWAITING FOR LOADING ELEMENT⏰({timeout}s) \nselector:::",
        selector,
        "\nxpath:::",
        xpath,
    )

    if isGoOnTop:
        await goOnTopBrowser(tab=tab)

    try:
        # Wrap element finding in asyncio timeout to ensure it doesn't hang indefinitely
        async def _find_elements():
            if selector:
                if typeFind == "multi":
                    elements = await tab.select_all(selector, timeout)
                    return elements
                else:
                    elements = await tab.select_all(selector, timeout)
                    
                    # Check if elements list is empty
                    if not elements or len(elements) == 0:
                        raise IndexError("Element not found - empty elements list")

                    elmChose = None

                    if text:
                        for elm in elements:
                            if isContains:
                                if text.strip().lower() in elm.text:
                                    print("🦋🦋🦋 Element:::", elm)
                                    elmChose = elm
                                    break
                            else:
                                if text == elm.text:
                                    print("🦋🦋🦋 Element:::", elm)
                                    elmChose = elm
                                    break
                    else:
                        elm = elements[0]
                        elmChose = elm

                    if not elmChose:
                        raise Exception("Element not found")

                    return elmChose

            else:
                elements = await tab.xpath(xpath=xpath, timeout=timeout)
                if typeFind == "multi":
                    return elements
                else:
                    # Check if elements list is empty before accessing index
                    if not elements or len(elements) == 0:
                        raise IndexError("Element not found - empty elements list")
                    element = elements[0]
                    if not element:
                        raise Exception("Element not found")
                    return element
        
        # Add extra 5 seconds buffer to the timeout to account for any delays
        try:
            return await asyncio.wait_for(_find_elements(), timeout=timeout + 5)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Element finding timed out after {timeout + 5} seconds")
            
    except IndexError as e:
        # Re-raise IndexError with more context
        raise IndexError(f"Element not found after timeout: {e}")
    except TimeoutError as e:
        # Re-raise timeout errors
        raise
    except Exception as e:
        raise Exception("🔴🦋🦋🦋🔴Get element err:", e)


async def sendKey(
    tab: nd.Tab,
    contentInput: str,
    text: str = None,
    rootTag: ElementsTag = "input",
    attributes: Dict[AttributesTag, str] = None,
    parentAttributes: Dict[AttributesTag, str] = None,
    parentTag: ElementsTag = None,
    isEnter: bool = False,
    timeout: float = 30,
    timeDelay: float = 0,
    timeDelayAction: float = 0,
    typeSendKey: Literal["fast", "sendKey", "human"] = "sendKey",
    numberActionFakePerson: int = 1,
    scrollToElement: Literal["vertical", "horizontal"] = None,
    isRemove: bool = True,
    isGoOnTop: bool = False,
    splitKeyword: str = None,
) -> bool:
    """
    Send keys to input element
    """
    if timeDelay > 0:
        await asyncio.sleep(timeDelay)

    elm = await getElement(
        tab=tab,
        rootTag=rootTag,
        attributes=attributes,
        parentTag=parentTag,
        parentAttributes=parentAttributes,
        timeout=timeout,
        text=text,
    )
    if not elm:
        raise Exception("Element not found")

    if numberActionFakePerson:
        await humanLikeMouseMovement(tab=tab, max_movements=numberActionFakePerson)

    if scrollToElement == "vertical":
        await elm.scroll_into_view()
        await asyncio.sleep(0.5)

    contentInput = contentInput.replace("\n", ". ")

    maxAttempts = 3
    for attempt in range(maxAttempts):
        try:

            if timeDelayAction > 0:
                await asyncio.sleep(timeDelayAction)

            if isGoOnTop:
                await goOnTopBrowser(tab=tab)

            if isRemove:
                # Thử nhiều cách clear cho contenteditable
                try:

                    selector = buildSelector(
                        rootTag=rootTag,
                        attributes=attributes,
                        parentAttributes=parentAttributes,
                        parentTag=parentTag,
                    )
                    await tab.evaluate(
                        f"""
                            document.querySelector('{selector}').innerHTML = '';
                        """
                    )
                    await elm.clear_input()
                except:
                    # Cách 3: Clear input truyền thống
                    await elm.clear_input()
                await asyncio.sleep(1)

            if typeSendKey == "fast":
                selector = buildSelector(
                    rootTag=rootTag,
                    attributes=attributes,
                    parentAttributes=parentAttributes,
                    parentTag=parentTag,
                )

                success = None
                if not splitKeyword:
                    # Không có xuống hàng => gửi trực tiếp
                    success = await sendKeyUniversalAdvanced(
                        tab, selector, contentInput
                    )
                else:
                    parts = _splitContentBySpeaker(
                        contentInput, splitKeyword=splitKeyword
                    )

                    print(f"📝 Content split into {len(parts)} parts:")
                    contentInputBreakLine = "\n".join(parts)

                    print(f"📝 contentInputBreakLine:", contentInputBreakLine)
                    success = await sendKeyUniversalAdvanced(
                        tab, selector, contentInputBreakLine
                    )

                if not success:
                    await elm.send_keys(text=contentInput)

                # Simulate some human delay even with JS
                await asyncio.sleep(random.uniform(0.5, 1.0))
            elif typeSendKey == "human":
                # Type character by character using send_keys
                for char in contentInput:
                    await elm.send_keys(text=char)
                    await asyncio.sleep(random.uniform(0.02, 0.2))
            else:
                # Send all at once

                print("💬💬💬 ContentInput:", contentInput)
                await elm.send_keys(contentInput)

            if isEnter:
                await asyncio.sleep(1)
                # Send Enter key using element's send_keys method
                # await _sendEnterJS(tab=tab)
                await _sendEnterJS(elm)

            return True

        except Exception as e:
            print(f"Send key error (attempt {attempt+1}/{maxAttempts}): {e}")
            if attempt < maxAttempts - 1:
                await asyncio.sleep(1)

    print("Failed to send keys after multiple attempts.")
    return False


async def _sendShiftEnter(tab: nd.Tab):  # Sử dụng page/tab, không phải browser
    """Gửi Shift+Enter để xuống dòng mà không submit form"""
    await tab.send(
        nd.cdp.input_.dispatch_key_event(
            type_="keyDown",
            modifiers=8,  # 8 = Shift key
            key="Enter",
            code="Enter",
            windows_virtual_key_code=13,
        )
    )
    await tab.send(
        nd.cdp.input_.dispatch_key_event(
            type_="keyUp",
            modifiers=8,
            key="Enter",
            code="Enter",
            windows_virtual_key_code=13,
        )
    )


async def _sendEnterJS(element):
    js_function = "(item) => { item.dispatchEvent(new KeyboardEvent('keydown', {keyCode: 13, bubbles: true})); }"
    await element.apply(js_function)


async def _sendEnterComplete(element):
    """Version đầy đủ các keyboard events"""
    js_function = """
    (item) => { 
        item.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'Enter', 
            code: 'Enter', 
            which: 13, 
            keyCode: 13, 
            bubbles: true, 
            cancelable: true
        })); 
    }
    """
    await element.apply(js_function)


def _splitContentBySpeaker(content, splitKeyword="Speaker"):
    """
    Cắt nội dung thành các phần dựa trên từ khóa
    """

    # Split theo từ khóa, giữ lại từ khóa ở đầu mỗi phần
    parts = content.split(splitKeyword)

    # Bỏ phần đầu nếu rỗng và thêm lại từ khóa cho các phần còn lại
    result = []
    for i, part in enumerate(parts):
        if i == 0:
            # Phần đầu tiên (trước từ khóa đầu tiên)
            if part.strip():
                result.append(part.strip())
        else:
            # Các phần còn lại - thêm lại từ khóa
            clean_part = f"{splitKeyword}{part}".strip()
            if clean_part:
                result.append(clean_part)

    return result


async def sendKeyUniversalAdvanced(tab: nd.Tab, selector: str, content: str) -> bool:
    """Advanced universal input with multiple fallback methods"""

    escaped = content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

    # Method 1: execCommand (best for contenteditable)
    method1_success = await tab.evaluate(
        f"""
        (function() {{
            try {{
                const el = document.querySelector('{selector}');
                if (!el) return false;
                
                el.focus();
                el.click();
                
                if (el.isContentEditable) {{
                    // Clear and insert using execCommand
                    document.execCommand('selectAll', false, null);
                    document.execCommand('delete', false, null);
                    const success = document.execCommand('insertText', false, "{escaped}");
                    
                    if (success) {{
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                }}
                return false;
            }} catch (e) {{ return false; }}
        }})()
    """
    )

    if method1_success:
        print("✅ Method 1 (execCommand) succeeded")
        return True

    # Method 2: innerHTML for contenteditable, value for inputs
    method2_success = await tab.evaluate(
        f"""
        (function() {{
            try {{
                const el = document.querySelector('{selector}');
                if (!el) return false;
                
                el.focus();
                el.click();
                
                if (el.isContentEditable || el.tagName.toLowerCase() === 'div') {{
                    el.innerHTML = "{escaped}";
                }} else {{
                    el.value = "{escaped}";
                }}
                
                // Trigger events
                ['input', 'change', 'keyup'].forEach(eventType => {{
                    el.dispatchEvent(new Event(eventType, {{ bubbles: true }}));
                }});
                
                return true;
            }} catch (e) {{ return false; }}
        }})()
    """
    )

    if method2_success:
        print("✅ Method 2 (innerHTML/value) succeeded")
        return True

    # Method 3: textContent for contenteditable
    method3_success = await tab.evaluate(
        f"""
        (function() {{
            try {{
                const el = document.querySelector('{selector}');
                if (!el) return false;
                
                el.focus();
                
                if (el.isContentEditable || el.tagName.toLowerCase() === 'div') {{
                    el.textContent = "{escaped}";
                }} else {{
                    el.value = "{escaped}";
                }}
                
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                
                return true;
            }} catch (e) {{ return false; }}
        }})()
    """
    )

    if method3_success:
        print("✅ Method 3 (textContent) succeeded")
        return True

    print("❌ All methods failed")
    return False


async def click(
    tab: nd.Tab,
    text: str = None,
    rootTag: ElementsTag = None,
    attributes: Dict[AttributesTag, str] = None,
    parentTag: ElementsTag = None,
    parentAttributes: Dict[AttributesTag, str] = None,
    xOffset: int = 1,
    yOffset: int = 1,
    repetitions: int = 1,
    timeout: float = 30,
    timeDelay: float = 0,
    timeDelayAction: float = 0,
    numberActionFakePerson: int = 1,
    isContains: bool = True,
    typeFind: Literal["one", "multi"] = "one",
    scrollToElement: Literal["vertical", "horizontal"] = None,
    isGoOnTop: bool = False,
) -> bool:
    """
    Click on element
    """
    if timeDelay > 0:
        await asyncio.sleep(timeDelay)

    elm = await getElement(
        tab=tab,
        text=text,
        rootTag=rootTag,
        attributes=attributes,
        parentTag=parentTag,
        parentAttributes=parentAttributes,
        timeout=timeout,
        isContains=isContains,
        typeFind=typeFind,
    )
    if not elm:
        raise Exception("Element not found")

    if numberActionFakePerson:
        await humanLikeMouseMovement(tab=tab, max_movements=numberActionFakePerson)

    maxAttempts = 3
    for attempt in range(maxAttempts):
        try:

            # Add scrolling to element if requested
            if scrollToElement == "vertical":
                await elm.scroll_into_view()
                await asyncio.sleep(0.5)

            if timeDelayAction > 0:
                await asyncio.sleep(timeDelayAction)

            if isGoOnTop:
                await goOnTopBrowser(tab=tab)

            await elm.mouse_move()
            # await elm.flash()

            posElm = await elm.get_position()

            for _ in range(repetitions):
                if xOffset > 0 or yOffset > 0:
                    print("📍📍📍 Click location 📍📍📍")
                    await asyncio.sleep(0.2)
                    centerX = (posElm.x + posElm.width / 2) + xOffset
                    centerY = (posElm.y + posElm.height / 2) + yOffset
                    await tab.mouse_click(x=centerX, y=centerY, button="left")

                else:
                    print("🦋🦋🦋 Click element 🦋🦋🦋")
                    await asyncio.sleep(0.2)
                    await elm.mouse_click()

            return True

        except Exception as e:
            print(f"Click error (attempt {attempt+1}/{maxAttempts}): {e}")
            if attempt < maxAttempts - 1:
                await asyncio.sleep(1)

    raise Exception("Click error after multiple attempts")


async def clickOnElement(
    tab: nd.Tab,
    elm: nd.Element,
    xOffset: int = 1,
    yOffset: int = 1,
    repetitions: int = 1,
    timeDelay: float = 0,
    timeDelayAction: float = 0,
    numberActionFakePerson: int = 1,
    scrollToElement: Literal["vertical", "horizontal"] = None,
    isGoOnTop: bool = False,
) -> bool:
    """
    Click on element
    """
    if timeDelay > 0:
        await asyncio.sleep(timeDelay)

    if numberActionFakePerson:
        await humanLikeMouseMovement(tab=tab, max_movements=numberActionFakePerson)

    maxAttempts = 3
    for attempt in range(maxAttempts):
        try:

            # Add scrolling to element if requested
            if scrollToElement == "vertical":
                await elm.scroll_into_view()
                await asyncio.sleep(0.5)

            if timeDelayAction > 0:
                await asyncio.sleep(timeDelayAction)

            if isGoOnTop:
                await goOnTopBrowser(tab=tab)

            await elm.mouse_move()
            # await elm.flash()

            posElm = await elm.get_position()

            for _ in range(repetitions):
                if xOffset > 0 or yOffset > 0:
                    print("📍📍📍 Click location 📍📍📍")
                    await asyncio.sleep(0.2)
                    centerX = (posElm.x + posElm.width / 2) + xOffset
                    centerY = (posElm.y + posElm.height / 2) + yOffset
                    await tab.mouse_click(x=centerX, y=centerY, button="left")

                else:
                    print("🦋🦋🦋 Click element 🦋🦋🦋")
                    await asyncio.sleep(0.2)
                    await elm.mouse_click()

            return True

        except Exception as e:
            print(f"Click error (attempt {attempt+1}/{maxAttempts}): {e}")
            if attempt < maxAttempts - 1:
                await asyncio.sleep(1)

    raise Exception("Click error after multiple attempts")


async def dragAndDrop(
    tab: nd.Tab,
    sourceElement: nd.Element,
    targetElement: nd.Element,
    timeDelay: float = 0,
    steps: int = 5,
    isGoOnTop: bool = False,
) -> bool:
    """Drag and drop from source to target element"""

    if timeDelay > 0:
        await asyncio.sleep(timeDelay)

    try:
        # Get positions
        src_pos = await sourceElement.get_position()
        tgt_pos = await targetElement.get_position()

        # Calculate centers
        src_center = (src_pos.x + src_pos.width / 2, src_pos.y + src_pos.height / 2)
        tgt_center = (tgt_pos.x + tgt_pos.width / 2, tgt_pos.y + tgt_pos.height / 2)

        print(f"Dragging from {src_center} to {tgt_center}")

        # Try element's mouse_drag first
        await sourceElement.mouse_drag(destination=tgt_center, steps=steps)
        return True

    except Exception as e:
        print(f"Element drag failed: {e}, trying manual...")

        try:
            # Manual drag fallback
            if isGoOnTop:
                await goOnTopBrowser(tab=tab)

            await tab.mouse.move(*src_center)
            await tab.mouse.down()

            # Smooth movement
            x_step = (tgt_center[0] - src_center[0]) / steps
            y_step = (tgt_center[1] - src_center[1]) / steps

            for i in range(1, steps + 1):
                x = src_center[0] + x_step * i
                y = src_center[1] + y_step * i
                await tab.mouse.move(x, y)
                await asyncio.sleep(0.1)

            await tab.mouse.up()
            print("✅ Manual drag completed")
            return True

        except Exception as e2:
            print(f"❌ All drag methods failed: {e2}")
            return False


async def takeScreenshot(
    tab: nd.Tab,
    fileName: str = "screenshot.png",
    fullPage: bool = False,
    isGoOnTop: bool = False,
) -> bool:
    """
    Take a screenshot of the page or element
    """
    if isGoOnTop:
        await goOnTopBrowser(tab=tab)

    try:

        if fullPage:
            # Take full page screenshot using save_screenshot method
            await tab.save_screenshot(fileName, full_page=True)
        else:
            # Take viewport screenshot
            await tab.save_screenshot(fileName)

        print(f"✅ Screenshot saved: {fileName}")
        return True

    except Exception as e:
        print(f"❌ Error taking screenshot: {e}")
        return False


async def takeElementScreenshot(
    elm: nd.Element,
    fileName: str = "element_screenshot.png",
    scale: float = 1.0,
) -> bool:
    """
    Take a screenshot of specific element
    """
    try:
        # Use save_screenshot method that exists in Element class
        await elm.save_screenshot(fileName, scale=scale)
        print(f"✅ Element screenshot saved: {fileName}")
        return True

    except Exception as e:
        print(f"❌ Error taking element screenshot: {e}")
        return False


async def takeElementScreenshot(
    elm: nd.Element,
    fileName: str = "element_screenshot.png",
    scale: float = 1.0,
) -> bool:
    """
    Take a screenshot of specific element
    """
    try:
        # Use save_screenshot method that exists in Element class
        await elm.save_screenshot(fileName, scale=scale)
        print(f"✅ Element screenshot saved: {fileName}")
        return True

    except Exception as e:
        print(f"❌ Error taking element screenshot: {e}")
        return False


async def goOnTopBrowser(tab: nd.Tab):
    try:
        resultCheckVisibility = await UtilActionsBrowser.checkBrowserVisibility(
            tab=tab, threshold_percentage=95
        )
        if resultCheckVisibility["is_actually_obscured"]:
            await UtilActionsBrowser.bringBrowserToTop(tab=tab)
    except:
        pass


async def scrollElementToTopOrBottom(
    tab: nd.Tab,
    position: Literal["top", "bottom"] = "top",
    rootTag: ElementsTag = None,
    attributes: Dict[AttributesTag, str] = None,
    parentTag: ElementsTag = None,
    parentAttributes: Dict[AttributesTag, str] = None,
    text: str = None,
    isContains: bool = True,
    timeout: float = 30,
    timeDelay: float = 0,
    timeDelayAction: float = 0,
    numberActionFakePerson: int = 1,
    isGoOnTop: bool = False,
) -> bool:
    """
    Scroll element to top or bottom using mouse wheel events
    """
    if timeDelay > 0:
        await asyncio.sleep(timeDelay)

    elm = await getElement(
        tab=tab,
        rootTag=rootTag,
        attributes=attributes,
        parentTag=parentTag,
        parentAttributes=parentAttributes,
        timeout=timeout,
        text=text,
        isContains=isContains,
        isGoOnTop=isGoOnTop,
    )
    if not elm:
        raise Exception("Element not found")

    if numberActionFakePerson:
        await humanLikeMouseMovement(tab=tab, max_movements=numberActionFakePerson)
    
    # Move mouse to element to simulate user focus
    await elm.mouse_move()
    
    # Get element position for the wheel event target
    pos_elm = await elm.get_position()
    center_x = pos_elm.x + pos_elm.width / 2
    center_y = pos_elm.y + pos_elm.height / 2

    if timeDelayAction > 0:
        await asyncio.sleep(timeDelayAction)

    # Use mouse wheel to scroll
    # 100 is a rough standard scroll tick. Positive for down (bottom), negative for up (top).
    delta_y = 100 if position != "top" else -100
    
    # Scroll multiple times to simulate reading/scrolling or reaching the end
    # We use a loop to send multiple events
    num_scrolls = 20
    
    print(f"🖱️ Scrolling {position} {num_scrolls} times...")
    
    for _ in range(num_scrolls):
        await tab.send(
            nd.cdp.input_.dispatch_mouse_event(
                type_="mouseWheel",
                x=center_x,
                y=center_y,
                delta_x=0,
                delta_y=delta_y
            )
        )
        # Small delay between scrolls to mimic human speed and allow UI updates
        await asyncio.sleep(random.uniform(0.1, 0.3))
    
    return True


async def zoomPage(
    tab: nd.Tab,
    action: Literal["in", "out", "reset", "custom"] = "in",
    times: int = 1,
    customScale: float = None
) -> bool:
    """
    Zoom page using OS-level Input (Win32 API).
    TRULY mimics "Hold Ctrl + Scroll" by sending physical background input events.
    Requires pywin32.
    
    action: "in", "out", "reset", "custom"
    customScale: Target devicePixelRatio (e.g. 0.5 for 50%). Used when action="custom".
    """
    if not win32api or not win32con:
        print("❌ Win32 API not available. Cannot perform physical zoom.")
        return False
        
    try:
        import win32gui
    except ImportError:
        print("❌ Win32 GUI not available.")
        return False

    try:
        # 1. Helper to find window and move mouse
        async def activate_window_and_move_mouse():
            try:
                # Mark window to find it
                original_title = await tab.evaluate("document.title")
                unique_id = str(int(time.time() * 1000))
                marked_title = f"{original_title}_{unique_id}"
                await tab.evaluate(f"document.title = '{marked_title}';")
                await asyncio.sleep(0.2)
                
                found_hwnd = None
                def callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if marked_title in title:
                            windows.append(hwnd)
                
                hwnds = []
                win32gui.EnumWindows(callback, hwnds)
                
                if hwnds:
                    hwnd = hwnds[0]
                    # Bring to top
                    try:
                        win32gui.SetForegroundWindow(hwnd)
                    except:
                        # Sometimes fails if user is doing something else, try generic bringToTop
                        pass
                        
                    # Get Screen Coordinates
                    rect = win32gui.GetWindowRect(hwnd)
                    x, y, w, h = rect
                    center_x = (x + w) // 2
                    center_y = (y + h) // 2
                    
                    # Move Physical Mouse
                    win32api.SetCursorPos((center_x, center_y))
                    
                    # Small click to ensure focus
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    
                    print(f"Moved mouse to {center_x}, {center_y}")
                else:
                    print("Window not found for mouse movement")
                
                # Restore title
                await tab.evaluate(f"document.title = '{original_title}';")
                
            except Exception as e:
                print(f"Auto-focus error: {e}")

        await activate_window_and_move_mouse()
        await asyncio.sleep(0.5) 
        
        # Helper to get current DPR
        async def get_dpr():
            val = await tab.evaluate("window.devicePixelRatio")
            return float(val) if val else 1.0

        current_dpr = await get_dpr()
            
        # Helper: Send Ctrl + Key
        def send_zoom_key(direction: Literal["in", "out"]):
            # Press Ctrl
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            time.sleep(0.1)
            
            # Press +/-
            # VK_OEM_PLUS = 0xBB (+)
            # VK_OEM_MINUS = 0xBD (-)
            key_code = 0xBB if direction == "in" else 0xBD
            
            win32api.keybd_event(key_code, 0, 0, 0)
            time.sleep(0.1)
            
            # Release +/-
            win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            # Release Ctrl
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        
        # Helper: Send Ctrl + 0 (Reset)
        def send_ctrl_zero():
            print("Sending Ctrl+0 (Reset)...")
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            time.sleep(0.1)
            win32api.keybd_event(0x30, 0, 0, 0)
            time.sleep(0.1)
            win32api.keybd_event(0x30, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

        # Execution Logic
        if action == "reset":
            send_ctrl_zero()
            await asyncio.sleep(0.5)
            # Verify if it worked
            print(f"DPR after reset: {await get_dpr()}")
            return True

        target_dpr = None
        if action == "custom" and customScale is not None:
            target_dpr = float(customScale)
            print(f"Targeting DPR: {target_dpr}")
            
            # Reset first
            send_ctrl_zero()
            await asyncio.sleep(0.5)
        
        max_attempts = 60 if target_dpr else times
        
        for i in range(max_attempts):
            step_action = None
            
            if target_dpr is not None:
                dpr = await get_dpr()
                if abs(dpr - target_dpr) < 0.1:
                    print(f"Reached target DPR: {dpr}")
                    break
                
                if dpr > target_dpr:
                    step_action = "out"
                else:
                    step_action = "in"
                    
                print(f"Current: {dpr}, Target: {target_dpr} -> Zoom {step_action}")
            else:
                step_action = "in" if action == "in" else "out"
            
            # Perform physical action
            send_zoom_key(step_action)
            await asyncio.sleep(0.5) # Allow browser animation time
            
        final_dpr = await get_dpr()
        print(f"Final DPR: {final_dpr}")
        return True
        
    except Exception as e:
        print(f"Error zooming page: {e}")
        return False



async def click_base_on_element(
    driver: nd.Tab,
    elm: nd.Element,
    x_offset: Optional[int] = None,
    y_offset: Optional[int] = None,
    repetitions: int = 1,
    time_delay: float = 1,
    number_action_fake_person: int = 1,
    type_click: Literal["core", "location"] = "core",
):
    """
    Click on an element with various options and retry logic.
    
    Args:
        driver (nd.Tab): The nodriver Tab instance to control the browser.
        elm (nd.Element): The Element to click on.
        x_offset (int, optional): X offset from the element's origin. Default is None.
        y_offset (int, optional): Y offset from the element's origin. Default is None.
        repetitions (int, optional): Number of times to repeat the click action. Default is 1.
        time_delay (float, optional): Wait time in seconds before executing. Default is 1 second.
        number_action_fake_person (int, optional): Number of random mouse movements to simulate human behavior. Default is 1.
        type_click (Literal["core", "location"], optional): Type of click ("core" for direct click, "location" for mouse position click). Default is "core".
    
    Raises:
        Exception: If click fails after all retry attempts.
    """
    if time_delay > 0:
        await asyncio.sleep(time_delay)

    await random_mouse_jiggle(driver=driver, number_action_fake_person=number_action_fake_person)

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            position = await elm.get_position()
            width = position.width
            height = position.height
            
            for idx in range(repetitions):
                if x_offset is not None and y_offset is not None:
                    # Calculate center point and apply offset
                    center_x = position.x + width / 2
                    center_y = position.y + height / 2
                    target_x = center_x - width // 2 + x_offset
                    target_y = center_y - height // 2 + y_offset
                    
                    await driver.mouse_move(x=target_x, y=target_y)
                    await driver.mouse_click(x=target_x, y=target_y, button="left")
                else:
                    if type_click == "core":
                        logger.debug("🥝Click core🥝")
                        is_in_view = await is_elm_in_viewport(
                            driver=driver, element=elm
                        )
                        logger.debug(f"elm position::: {position}")
                        logger.debug(f"is_in_view::: {is_in_view}")
                        
                        # For nodriver, we can use element.click() or mouse click
                        try:
                            await elm.click()
                        except:
                            # Fallback to mouse click at element center
                            center_x = position.x + width / 2
                            center_y = position.y + height / 2
                            await driver.mouse_click(x=center_x, y=center_y, button="left")
                    else:
                        logger.debug("📍Click location📍")
                        is_in_view = await is_elm_in_viewport(
                            driver=driver, element=elm
                        )
                        logger.debug(f"elm position::: {position}")
                        logger.debug(f"is_in_view::: {is_in_view}")
                        
                        center_x = position.x + width / 2
                        center_y = position.y + height / 2
                        await driver.mouse_move(x=center_x, y=center_y)
                        await driver.mouse_click(x=center_x, y=center_y, button="left")
                
                await asyncio.sleep(0.2)

            return

        except Exception as e:
            logger.warning(f"Click Error::: {e}")
            logger.info(
                f"Retrying... ({attempt+1}/{max_attempts})"
            )
            await asyncio.sleep(1)
            # Re-fetch element position for next attempt
            try:
                position = await elm.get_position()
            except:
                raise Exception("Element became stale, cannot retry")

    raise Exception("Click error: Failed after all retry attempts")


async def is_elm_in_viewport(
    driver: nd.Tab,
    element: nd.Element,
    percent_horizontal: float = 30,
    percent_vertical: float = 30,
) -> bool:
    """
    Check if element is in viewport.
    
    Args:
        driver (nd.Tab): The nodriver Tab instance.
        element (nd.Element): Element to check.
        percent_horizontal (float, optional): Horizontal visibility percentage threshold. Default is 30.
        percent_vertical (float, optional): Vertical visibility percentage threshold. Default is 30.
    
    Returns:
        bool: True if element is sufficiently visible in viewport, False otherwise.
    """
    try:
        # Get viewport size
        viewport_info = await driver.evaluate("""
            () => ({
                width: window.innerWidth,
                height: window.innerHeight,
                x_offset: window.pageXOffset,
                y_offset: window.pageYOffset
            })
        """)
        
        window_width = viewport_info["width"]
        window_height = viewport_info["height"]
        window_x_offset = viewport_info["x_offset"]
        window_y_offset = viewport_info["y_offset"]

        # Get element bounding rect using element evaluation
        rect_info = await element.evaluate("""
            (el) => {
                const rect = el.getBoundingClientRect();
                return {
                    yStart: rect.top,
                    yEnd: rect.bottom,
                    height: rect.height,
                    width: rect.width,
                    xStart: rect.left,
                    xEnd: rect.right
                };
            }
        """)

        # Get element position information
        element_left = rect_info["xStart"] + window_x_offset  # Convert to absolute coordinates
        element_right = rect_info["xEnd"] + window_x_offset
        element_top = rect_info["yStart"] + window_y_offset
        element_bottom = rect_info["yEnd"] + window_y_offset
        element_width = rect_info["width"]
        element_height = rect_info["height"]

        # Calculate viewport boundaries
        viewport_left = window_x_offset
        viewport_right = window_x_offset + window_width
        viewport_top = window_y_offset
        viewport_bottom = window_y_offset + window_height

        # Check if element intersects with viewport
        is_visible_horizontally = (element_left < viewport_right) and (
            element_right > viewport_left
        )
        is_visible_vertically = (element_top < viewport_bottom) and (
            element_bottom > viewport_top
        )

        # If not fully visible, check overlap percentage
        if is_visible_horizontally and is_visible_vertically:
            # Calculate overlap area
            overlap_left = max(element_left, viewport_left)
            overlap_right = min(element_right, viewport_right)
            overlap_top = max(element_top, viewport_top)
            overlap_bottom = min(element_bottom, viewport_bottom)

            overlap_width = overlap_right - overlap_left
            overlap_height = overlap_bottom - overlap_top

            # Calculate overlap ratio relative to element size
            horizontal_overlap_ratio = overlap_width / element_width if element_width > 0 else 0
            vertical_overlap_ratio = overlap_height / element_height if element_height > 0 else 0

            # Get element info for logging
            try:
                tag_name = await element.evaluate("el => el.tagName")
                element_text = await element.evaluate("el => el.textContent || el.innerText || ''")
                logger.debug(f"element::: {{'tag': '{tag_name}', 'text': '{element_text[:50]}...'}}")
            except:
                pass

            # Check if at least the specified percentage is visible
            return (
                horizontal_overlap_ratio * 100 >= percent_horizontal
                and vertical_overlap_ratio * 100 >= percent_vertical
            )

        return False
    except Exception as e:
        logger.debug(f"Error checking element in viewport: {e}")
        return False


async def random_mouse_jiggle(driver: nd.Tab, number_action_fake_person: int = 3):
    """
    Move mouse randomly to simulate human behavior.
    
    Args:
        driver (nd.Tab): The nodriver Tab instance to control the browser.
        number_action_fake_person (int, optional): Number of random mouse movements to simulate human behavior. Default is 3.
    """
    if number_action_fake_person < 1:
        return
    
    try:
        viewport_info = await driver.evaluate("""
            () => ({
                width: window.innerWidth,
                height: window.innerHeight
            })
        """)
        
        width = viewport_info["width"] // 5
        height = viewport_info["height"] // 5

        body = await driver.query_selector("body")
        if not body:
            return

        body_position = await body.get_position()
        base_x = body_position.x
        base_y = body_position.y

        for _ in range(number_action_fake_person):
            x_offset = random.randint(0, width)
            y_offset = random.randint(0, height)
            try:
                target_x = base_x + x_offset
                target_y = base_y + y_offset
                await driver.mouse_move(x=target_x, y=target_y)
                await asyncio.sleep(random.uniform(0.05, 0.1))
                await driver.mouse_move(x=target_x + random.randint(-10, 10), y=target_y + random.randint(-10, 10))
                await asyncio.sleep(random.uniform(0.05, 0.1))
            except Exception as e:
                logger.debug(f"Mouse movement error: {e}")

    except Exception as e:
        logger.warning(f"Something went wrong when moving the mouse!!! {e}")

