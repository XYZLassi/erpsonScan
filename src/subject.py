import functools
from typing import TypeVar, Generic, Callable, Optional

T = TypeVar('T')
Observer = Callable[[T], None]


class Subject(Generic[T]):
    def __init__(self):
        self.observers: list[Observer] = list()

    def notify(self, data: T) -> T:
        for observer in self.observers:
            observer(data)

        return data

    def attach(self, observer: Observer) -> Optional[Callable[[], bool]]:
        if observer not in self.observers:
            self.observers.append(observer)
            return functools.partial(self.detach, observer)

        return None

    def detach(self, observer: Observer) -> bool:
        if observer in self.observers:
            self.observers.remove(observer)
            return True

        return False
