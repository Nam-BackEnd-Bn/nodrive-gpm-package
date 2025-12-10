import asyncio
import ai_image_voice.utils.UtilChecker as UtilChecker
from typing import List, Literal, Union, Optional
from Levenshtein import distance
import nodriver as nd


async def getSvgElement(page: nd.Tab, hrefValue: str) -> Optional[nd.Element]:
    """
    Find an SVG element based on its xlink:href attribute value.

    Args:
        page: NoDriver Tab instance
        hrefValue: The value of the xlink:href attribute (e.g., "#icon-settings")

    Returns:
        The Element representing the SVG element
    """
    print("🖼️🖼️🖼️ Get SVG  🖼️🖼️🖼️")

    try:
        # XPath expression for SVG use elements
        xpathExpression = (
            f"//*[local-name()='use' and @*[local-name()='href']='{hrefValue}']"
        )

        # Wait for element to be present
        for attempt in range(10):  # 10 second timeout
            try:
                element = await page.find(xpathExpression, timeout=1)
                if element:
                    print(f"✅ Found SVG element with href: {hrefValue}")
                    return element
            except:
                await asyncio.sleep(1)

        raise Exception(f"SVG element with href '{hrefValue}' not found")

    except Exception as e:
        print(f"❌ Error finding SVG element: {e}")
        raise Exception(e)


async def getElementByXpath(
    page: nd.Tab,
    xpath: str,
    timeout: int = 60,
    typeFind: Literal["click", "get", "multi", "selected"] = "get",
    isGetFull: bool = False,
    isGetHidden: bool = False,
) -> Union[nd.Element, List[nd.Element], None]:
    """
    Get element(s) by XPath with various find types for nodriver

    Args:
        page: NoDriver Tab instance
        xpath: XPath expression
        timeout: Timeout in seconds
        typeFind: Type of find operation
        isGetFull: Return all elements (for multi)
        isGetHidden: Return hidden elements

    Returns:
        Element, list of elements, or None
    """
    # print("🔍🔍🔍 Get element by xpath 🔍🔍🔍")

    if typeFind == "get":
        return await _getElementBasic(page, xpath, timeout, isGetHidden)
    elif typeFind == "click":
        return await _getElementClickable(page, xpath, timeout)
    elif typeFind == "multi":
        return await _getElementsMultiple(page, xpath, timeout, isGetFull)
    elif typeFind == "selected":
        return await _getElementSelected(page, xpath, timeout)


async def _getElementBasic(
    page: nd.Tab, xpath: str, timeout: int, isGetHidden: bool = False
) -> Optional[nd.Element]:
    """Get basic element with presence check"""

    try:
        # Wait for element with timeout
        element = await page.find(xpath, timeout=timeout)

        if not element:
            raise Exception("Element not found")

        if isGetHidden:
            return element

        # Get element properties
        box = await element.get_box_model()
        if not box:
            print("Get elm try again - no box model")
            await asyncio.sleep(1)
            element = await page.find(xpath, timeout=timeout)

        # Check if element has valid dimensions and position
        content = box.get("content", []) if box else []
        if len(content) >= 4:
            width = content[4] - content[0]  # right - left
            height = content[5] - content[1]  # bottom - top
            x = content[0]
            y = content[1]

            if width == 0 and height == 0 and x <= 0 and y <= 0:
                print("Get elm try again - invalid dimensions")
                await asyncio.sleep(1)
                element = await page.find(xpath, timeout=timeout)

        # Check if element is in viewport
        isInView = await UtilChecker.isElmInViewPort(page=page, element=element)

        # Get element info for logging
        tag_name = await element.get_attribute("tagName") or "unknown"
        text_content = await element.get_text() or ""

        print(
            "elm attrs:::",
            tag_name.lower(),
            text_content,
            f"box: {box}" if box else "no box",
        )

        # Check in viewport and not covered by other elements
        if not isInView:
            raise Exception("Element not in view")

        await asyncio.sleep(1)
        return element

    except Exception as e:
        print(f"❌ Error getting basic element: {e}")
        raise Exception(e)


async def _getElementClickable(
    page: nd.Tab, xpath: str, timeout: int
) -> Optional[nd.Element]:
    """Get clickable element"""

    try:
        element = await page.find(xpath, timeout=timeout)

        if not element:
            raise Exception("Element not found")

        # Check if element is clickable (visible and enabled)
        is_displayed = await element.evaluate("el => el.offsetParent !== null")
        is_enabled = await element.evaluate("el => !el.disabled")

        if not (is_displayed and is_enabled):
            raise Exception("Element not clickable")

        # Get element properties for validation
        box = await element.get_box_model()
        if box:
            content = box.get("content", [])
            if len(content) >= 4:
                width = content[4] - content[0]
                height = content[5] - content[1]
                x = content[0]
                y = content[1]

                if width == 0 and height == 0 and x <= 0 and y <= 0:
                    print("Get elm try again - invalid click area")
                    await asyncio.sleep(1)
                    element = await page.find(xpath, timeout=timeout)

        isInView = await UtilChecker.isElmInViewPort(page=page, element=element)

        # Get element info
        tag_name = await element.get_attribute("tagName") or "unknown"
        text_content = await element.get_text() or ""

        print(
            "elm attrs:::",
            tag_name.lower(),
            text_content,
            f"box: {box}" if box else "no box",
        )

        if not isInView:
            raise Exception("Element not in view")

        await asyncio.sleep(1)
        return element

    except Exception as e:
        print(f"❌ Error getting clickable element: {e}")
        raise Exception(e)


async def _getElementsMultiple(
    page: nd.Tab, xpath: str, timeout: int, isGetFull: bool = False
) -> List[nd.Element]:
    """Get multiple elements"""

    try:
        print("Get multi")

        # Find all elements matching xpath
        elements = await page.find_all(xpath, timeout=timeout)

        if not elements:
            raise Exception("No elements found")

        if isGetFull:
            return elements

        # Filter visible elements
        listVisibleElm = []
        for elm in elements:
            try:
                # Check if element is displayed
                is_displayed = await elm.evaluate("el => el.offsetParent !== null")
                isInView = await UtilChecker.isElmInViewPort(
                    page=page, element=elm
                )

                if is_displayed and isInView:
                    listVisibleElm.append(elm)
            except Exception as e:
                print(f"⚠️ Error checking element visibility: {e}")
                continue

        return listVisibleElm

    except Exception as e:
        print(f"❌ Error getting multiple elements: {e}")
        raise Exception(e)


async def _getElementSelected(
    page: nd.Tab, xpath: str, timeout: int
) -> Optional[nd.Element]:
    """Get selected element (for select/option elements)"""

    try:
        element = await page.find(xpath, timeout=timeout)

        if not element:
            raise Exception("Element not found")

        # Check if element is selected (for select options, checkboxes, radio buttons)
        is_selected = await element.evaluate(
            """
            el => {
                if (el.tagName === 'OPTION') return el.selected;
                if (el.type === 'checkbox' || el.type === 'radio') return el.checked;
                return el.selected || false;
            }
        """
        )

        if not is_selected:
            raise Exception("Element not selected")

        # Validate element properties
        box = await element.get_box_model()
        if box:
            content = box.get("content", [])
            if len(content) >= 4:
                width = content[4] - content[0]
                height = content[5] - content[1]
                x = content[0]
                y = content[1]

                if width == 0 and height == 0 and x <= 0 and y <= 0:
                    print("Get elm try again - invalid selected element")
                    await asyncio.sleep(1)
                    element = await page.find(xpath, timeout=timeout)

        isInView = await UtilChecker.isElmInViewPort(page=page, element=element)

        # Get element info
        tag_name = await element.get_attribute("tagName") or "unknown"
        text_content = await element.get_text() or ""

        print(
            "elm attrs:::",
            tag_name.lower(),
            text_content,
            f"box: {box}" if box else "no box",
        )

        if not isInView:
            raise Exception("Element not in view")

        await asyncio.sleep(1)
        return element

    except Exception as e:
        print(f"❌ Error getting selected element: {e}")
        raise Exception(e)


async def getElmTextTopScore(listElmText: List[nd.Element], inputText: str) -> List:
    """
    Find element with text that best matches input text using Levenshtein distance

    Args:
        listElmText: List of NoDriver Elements
        inputText: Text to match against

    Returns:
        List containing [best_element, score]
    """

    async def findBestMatch(inputText: str, listTexts: List[str]):
        # Convert to lowercase for case-insensitive comparison
        inputTextLower = inputText.lower()
        listTextsLower = [text.lower() for text in listTexts]

        # Calculate Levenshtein distance, choose input with smallest distance
        bestMatchLower = min(listTextsLower, key=lambda x: distance(inputTextLower, x))
        minDistance = distance(inputTextLower, bestMatchLower)
        maxLen = max(len(inputTextLower), len(bestMatchLower))
        score = (1 - minDistance / maxLen) * 100  # Convert to percentage similarity

        # Get original value of bestMatch from listTexts
        bestMatch = listTexts[listTextsLower.index(bestMatchLower)]
        return bestMatch, score

    # Get text from all elements
    listTexts = []
    for element in listElmText:
        try:
            text = await element.get_text() or ""
            listTexts.append(text)
        except Exception as e:
            print(f"⚠️ Error getting text from element: {e}")
            listTexts.append("")

    print("🗟 ListTexts:::", listTexts)

    bestOutput, score = await findBestMatch(inputText=inputText, listTexts=listTexts)

    indexText = listTexts.index(bestOutput)
    elm = listElmText[indexText]

    print("🔝 BestInput:::", bestOutput)
    print("💯 Score:::", score)

    # Get element info for logging
    try:
        tag_name = await elm.get_attribute("tagName") or "unknown"
        box = await elm.get_box_model()
        print(
            "🔘 Elm:::",
            tag_name.lower(),
            f"box: {box}" if box else "no box",
        )
    except Exception as e:
        print(f"⚠️ Error getting element info: {e}")

    # If score is low, try exact substring match
    if score < 70:
        for i, elmText in enumerate(listElmText):
            try:
                element_text = await elmText.get_text() or ""
                print("inputText:::", inputText)
                print("elmText.text:::", element_text)
                if element_text in inputText:
                    return [elmText, 100]
            except Exception as e:
                print(f"⚠️ Error in substring match: {e}")
                continue

    return [listElmText[indexText], score]
