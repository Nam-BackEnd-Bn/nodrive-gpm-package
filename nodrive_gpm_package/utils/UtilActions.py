import asyncio, time, random, nodriver as nd, re
from typing import Literal, Dict, List, Union
from utils import UtilActionsBrowser, UtilUserAgent

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
        if selector:
            if typeFind == "multi":
                elements = await tab.select_all(selector, timeout)
                return elements
            else:
                elements = await tab.select_all(selector, timeout)

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
                element = elements[0]
                if not element:
                    raise Exception("Element not found")
                return element
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
                await _sendEnterJS(tab=tab)

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
