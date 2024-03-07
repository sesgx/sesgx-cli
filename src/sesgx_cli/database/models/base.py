from sqlalchemy.orm import (
    DeclarativeBase,
    MappedAsDataclass,
)


class Base(DeclarativeBase, MappedAsDataclass):
    ...

    def to_string(self, keys: list[str]):
        props: dict[str, str | int | float] = {}

        for key in keys:
            value = self.__getattribute__(key)

            if type(value) == str:  # noqa: E721
                props[key] = f'"{value}"'

            elif type(value) in (int, float):
                props[key] = f"{value}"

        parameters = ", ".join(f"{k}={v}" for k, v in props.items())

        return f"{self.__class__.__name__}({parameters})"
