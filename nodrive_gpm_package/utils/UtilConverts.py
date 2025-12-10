def convertStrToArr(strVal: str, characterSplit: str = ",") -> list[str]:
    if strVal.strip() == "":
        return []
    listItems = [item.strip() for item in strVal.split(characterSplit)]
    listItems = [item for item in listItems if item.strip() != ""]
    return listItems


def convertArrToStr(arrVal: list[str], character_join: str = ", ") -> str:
    return character_join.join(arrVal)


def convertRemoveItemEmptyArr(arr: list[any]) -> list[any]:
    return [item for item in arr if item != "" and item != None]


def convertRemoveItemEmptyDict(arr: dict) -> dict:
    return {key: value for key, value in arr.items() if value not in [None, "", [], {}]}


def convertToLowercaseArr(strings: list[str]):
    return [s.lower() for s in strings]
