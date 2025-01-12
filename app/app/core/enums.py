from enum import Enum


class StrEnum(str, Enum):
    """
    StrEnum subclasses that create variants using `auto()` will have values equal to their names

    Enums inheriting from this class that set values using `enum.auto()` will have variant values
        equal to their names
    """

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[str]
    ) -> str:
        """
        Uses the name as the automatic value, rather than an integer
        """
        return name

    def __str__(self) -> str:
        return str(self.value)


    @classmethod
    def list_value(cls)-> list[str]:
        return [member.value for member in cls]
    
    
    @classmethod
    def has_value(cls, value: str)-> bool:
        return value in cls.list_value()