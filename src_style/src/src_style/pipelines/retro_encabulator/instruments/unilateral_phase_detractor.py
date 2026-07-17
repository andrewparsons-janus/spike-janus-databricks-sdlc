import dataclasses
import time

@dataclasses.dataclass(frozen=True)
class InverseReactiveCurrent:
    ohms: float = 42


def synchronize_cardinal_gram_meter() -> None:
    print("Automatically synchronizing cardinal gram-meter", end="")
    for _ in range(3):
        time.sleep(1)
        print(" . ", end="")
    print("\nDone.")
