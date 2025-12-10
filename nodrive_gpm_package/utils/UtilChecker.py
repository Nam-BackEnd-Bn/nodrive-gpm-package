import nodriver as nd
import logging


async def isElmInViewPort(
    tab: nd.Tab,
    element: nd.Element,
    percentHorizontal: float = 10,
    percentVertical: float = 10,
    debug: bool = False,
) -> bool:
    """
    Kiểm tra xem phần tử có nằm trong viewport không với thông tin debug đầy đủ cho NoDriver

    Args:
        page: NoDriver Tab instance
        element: NoDriver Element cần kiểm tra
        percentHorizontal: Phần trăm tối thiểu theo chiều ngang (default: 10%)
        percentVertical: Phần trăm tối thiểu theo chiều dọc (default: 10%)
        debug: Có hiển thị thông tin debug hay không (default: False)

    Returns:
        bool: True nếu element nằm trong viewport với đủ phần trăm yêu cầu
    """
    try:
        # Lấy thông tin viewport từ page sử dụng CDP
        viewport_result = await tab.send(
            nd.cdp.runtime.evaluate(
                expression="""
                () => ({
                    windowHeight: window.innerHeight,
                    windowWidth: window.innerWidth,
                    windowXOffset: window.pageXOffset || window.scrollX,
                    windowYOffset: window.pageYOffset || window.scrollY,
                    documentWidth: document.documentElement.scrollWidth,
                    documentHeight: document.documentElement.scrollHeight
                })
                """
            )
        )
        viewport_info = viewport_result.result.value

        # Lấy thông tin element sử dụng element.apply()
        element_info = await element.apply(
            """
            (element) => {
                const rect = element.getBoundingClientRect();
                const computedStyle = window.getComputedStyle(element);
                
                return {
                    // Thông tin getBoundingClientRect (relative to viewport)
                    yStart: rect.top,
                    yEnd: rect.bottom,
                    height: rect.height,
                    width: rect.width,
                    xStart: rect.left,
                    xEnd: rect.right,
                    
                    // Thông tin bổ sung
                    x: rect.x,
                    y: rect.y,
                    
                    // Kiểm tra element có thực sự visible không
                    isVisible: element.offsetParent !== null && 
                              computedStyle.display !== 'none' &&
                              computedStyle.visibility !== 'hidden' &&
                              computedStyle.opacity !== '0',
                    
                    // Thông tin scroll của window
                    windowScrollX: window.pageXOffset || window.scrollX,
                    windowScrollY: window.pageYOffset || window.scrollY,
                    
                    // Kích thước document
                    documentWidth: document.documentElement.scrollWidth,
                    documentHeight: document.documentElement.scrollHeight,
                    
                    // Kích thước viewport
                    viewportWidth: window.innerWidth,
                    viewportHeight: window.innerHeight,
                    
                    // Tag và text info
                    tagName: element.tagName,
                    elementText: element.textContent ? element.textContent.slice(0, 100) : '',
                    elementId: element.id || '',
                    elementClass: element.className || '',
                    
                    // Additional computed style info
                    display: computedStyle.display,
                    visibility: computedStyle.visibility,
                    opacity: computedStyle.opacity
                };
            }
            """
        )

        # Extract values for easier access
        window_height = viewport_info["windowHeight"]
        window_width = viewport_info["windowWidth"]
        window_x_offset = viewport_info["windowXOffset"]
        window_y_offset = viewport_info["windowYOffset"]

        # Tính toán tọa độ tuyệt đối
        element_left = element_info["xStart"] + window_x_offset
        element_right = element_info["xEnd"] + window_x_offset
        element_top = element_info["yStart"] + window_y_offset
        element_bottom = element_info["yEnd"] + window_y_offset
        element_width = element_info["width"]
        element_height = element_info["height"]

        # Tính toán ranh giới của viewport
        viewport_left = window_x_offset
        viewport_right = window_x_offset + window_width
        viewport_top = window_y_offset
        viewport_bottom = window_y_offset + window_height

        # Kiểm tra phần tử có giao với viewport không
        is_visible_horizontally = (element_left < viewport_right) and (
            element_right > viewport_left
        )
        is_visible_vertically = (element_top < viewport_bottom) and (
            element_bottom > viewport_top
        )

        # Initialize overlap ratios
        horizontal_overlap_ratio = 0
        vertical_overlap_ratio = 0
        result = False

        # Kiểm tra overlap và tính toán tỷ lệ
        if is_visible_horizontally and is_visible_vertically:
            # Tính độ giao nhau theo chiều ngang và dọc
            overlap_left = max(element_left, viewport_left)
            overlap_right = min(element_right, viewport_right)
            overlap_top = max(element_top, viewport_top)
            overlap_bottom = min(element_bottom, viewport_bottom)

            overlap_width = max(0, overlap_right - overlap_left)
            overlap_height = max(0, overlap_bottom - overlap_top)

            # Tính tỷ lệ giao nhau so với kích thước phần tử (avoid division by zero)
            if element_width > 0:
                horizontal_overlap_ratio = (overlap_width / element_width) * 100
            if element_height > 0:
                vertical_overlap_ratio = (overlap_height / element_height) * 100

            # Kiểm tra threshold
            result = (
                horizontal_overlap_ratio >= percentHorizontal
                and vertical_overlap_ratio >= percentVertical
            )

        # Log thông tin element - get additional element info for logging
        try:
            # Sử dụng NoDriver methods chính xác
            element_tag = element_info["tagName"]
            element_text = element_info["elementText"]
            logging.info(f"element::: tag={element_tag}, text={element_text[:50]}")
        except Exception as e:
            logging.warning(f"Could not get element info for logging: {e}")

        # Debug information nếu được yêu cầu
        if debug:
            print("\n" + "=" * 80)
            print("🔍 VIEWPORT CHECK DEBUG (NoDriver)")
            print("=" * 80)

            # Kết quả chính
            result_icon = "✅" if result else "❌"
            print(
                f"{result_icon} RESULT: Element {'IS' if result else 'IS NOT'} in viewport"
            )

            # Thông tin element
            print(f"\n📦 ELEMENT INFO:")
            print(f"   Tag: {element_info['tagName']}")
            print(f"   ID: {element_info['elementId'] or 'N/A'}")
            print(f"   Class: {element_info['elementClass'] or 'N/A'}")
            print(
                f"   Text: '{element_info['elementText']}{'...' if len(element_info['elementText']) >= 100 else ''}'"
            )

            # Get element position info từ NoDriver
            try:
                position = await element.get_position()
                print(
                    f"   NoDriver Position: x={position.x}, y={position.y}, w={position.width}, h={position.height}"
                )
            except Exception as e:
                print(f"   NoDriver Position: Error getting position - {e}")

            print(f"   Computed Size: {element_width}x{element_height}")
            print(f"   Is Visible: {element_info['isVisible']}")
            print(f"   Display: {element_info['display']}")
            print(f"   Visibility: {element_info['visibility']}")
            print(f"   Opacity: {element_info['opacity']}")

            # Vị trí element
            print(f"\n📍 ELEMENT POSITIONS:")
            print(
                f"   Relative to viewport: ({element_info['xStart']:.1f}, {element_info['yStart']:.1f}) to ({element_info['xEnd']:.1f}, {element_info['yEnd']:.1f})"
            )
            print(
                f"   Absolute positions: ({element_left:.1f}, {element_top:.1f}) to ({element_right:.1f}, {element_bottom:.1f})"
            )

            # Thông tin viewport
            print(f"\n🖥️ VIEWPORT:")
            print(f"   Size: {window_width}x{window_height}")
            print(f"   Scroll offset: ({window_x_offset}, {window_y_offset})")
            print(
                f"   Boundaries: ({viewport_left}, {viewport_top}) to ({viewport_right}, {viewport_bottom})"
            )
            print(
                f"   Document size: {element_info['documentWidth']}x{element_info['documentHeight']}"
            )

            # Phân tích overlap
            print(f"\n🔄 OVERLAP ANALYSIS:")
            print(
                f"   Required thresholds: H≥{percentHorizontal}%, V≥{percentVertical}%"
            )
            print(
                f"   Actual overlap: H={horizontal_overlap_ratio:.1f}%, V={vertical_overlap_ratio:.1f}%"
            )
            print(
                f"   Horizontal check: {'✅ PASS' if horizontal_overlap_ratio >= percentHorizontal else '❌ FAIL'}"
            )
            print(
                f"   Vertical check: {'✅ PASS' if vertical_overlap_ratio >= percentVertical else '❌ FAIL'}"
            )
            print(
                f"   Has any intersection: {'✅ YES' if (is_visible_horizontally and is_visible_vertically) else '❌ NO'}"
            )

            # Phân tích vấn đề tiềm ẩn
            print(f"\n⚠️ ANALYSIS:")
            issues = []

            if element_height > window_height:
                issues.append(
                    f"Element height ({element_height:.0f}px) > viewport height ({window_height}px)"
                )
            if element_width > window_width:
                issues.append(
                    f"Element width ({element_width:.0f}px) > viewport width ({window_width}px)"
                )
            if element_info["yStart"] < -window_height:
                issues.append(
                    f"Element far above viewport (top: {element_info['yStart']:.0f}px)"
                )
            elif element_info["yStart"] < 0:
                issues.append(
                    f"Element partially above viewport (top: {element_info['yStart']:.0f}px)"
                )
            if element_info["yStart"] > window_height:
                issues.append(
                    f"Element below viewport (top: {element_info['yStart']:.0f}px > viewport: {window_height}px)"
                )
            if element_info["xStart"] < -window_width:
                issues.append(
                    f"Element far left of viewport (left: {element_info['xStart']:.0f}px)"
                )
            elif element_info["xStart"] < 0:
                issues.append(
                    f"Element partially left of viewport (left: {element_info['xStart']:.0f}px)"
                )
            if element_info["xStart"] > window_width:
                issues.append(
                    f"Element right of viewport (left: {element_info['xStart']:.0f}px > viewport: {window_width}px)"
                )
            if not element_info["isVisible"]:
                issues.append(
                    "Element is hidden (display: none, visibility: hidden, opacity: 0, or no offsetParent)"
                )
            if not is_visible_horizontally:
                issues.append("No horizontal intersection with viewport")
            if not is_visible_vertically:
                issues.append("No vertical intersection with viewport")
            if is_visible_horizontally and is_visible_vertically and not result:
                issues.append(
                    f"Has intersection but insufficient overlap (H:{horizontal_overlap_ratio:.1f}% < {percentHorizontal}% or V:{vertical_overlap_ratio:.1f}% < {percentVertical}%)"
                )

            if issues:
                for issue in issues:
                    print(f"   • {issue}")
            else:
                print("   • No issues detected")

            # Suggestions
            if not result:
                print(f"\n💡 SUGGESTIONS:")
                if element_info["yStart"] > window_height or element_info["yEnd"] < 0:
                    print(
                        "   • Try scrolling element into view: await element.scroll_into_view()"
                    )
                    print(
                        "   • Or use: await tab.send(nd.cdp.dom.scroll_into_view_if_needed(node_id=element.node_id))"
                    )
                if (
                    horizontal_overlap_ratio < percentHorizontal
                    or vertical_overlap_ratio < percentVertical
                ):
                    print(
                        f"   • Consider lowering thresholds: percentHorizontal={max(5, horizontal_overlap_ratio-5):.0f}, percentVertical={max(5, vertical_overlap_ratio-5):.0f}"
                    )
                if element_height > window_height:
                    print(
                        "   • Element is taller than viewport - this is normal for long content"
                    )
                if not element_info["isVisible"]:
                    print(
                        "   • Check element visibility with CSS display/visibility/opacity properties"
                    )

            print("=" * 80)

        return result

    except Exception as e:
        if debug:
            print(f"❌ ERROR in viewport check: {e}")
            try:
                # Fallback để lấy element info
                element_tag = await element.apply("(el) => el.tagName") or "unknown"
                element_text = (
                    await element.apply("(el) => el.textContent?.slice(0, 50) || ''")
                    or ""
                )
                print(f"   Element tag: {element_tag}")
                print(f"   Element text: {element_text}")
            except Exception as inner_e:
                print(f"   Could not get element info: {inner_e}")
        return False
