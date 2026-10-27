"""Klasa bazowa encji eSterownik."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .catalog import EntitySpec
from .coordinator import EsterownikCoordinator


class EsterownikEntity(CoordinatorEntity[EsterownikCoordinator]):
    """Encja jednego rejestru sterownika."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: EsterownikCoordinator, spec: EntitySpec) -> None:
        super().__init__(coordinator)
        self.spec = spec
        self._attr_unique_id = f"{coordinator.info.mac}_{spec.vid}_{spec.tid}"
        self._attr_name = spec.name
        self._attr_device_info = coordinator.device_info
        self._attr_entity_registry_enabled_default = spec.enabled
        self._attr_entity_category = spec.category
        if spec.icon:
            self._attr_icon = spec.icon
        if spec.device_class:
            self._attr_device_class = spec.device_class

    @property
    def raw(self) -> str | None:
        """Surowa wartość rejestru stanu albo None."""
        return self.coordinator.value(self.spec.state_tid or self.spec.tid, self.spec.vid)

    @property
    def raw_float(self) -> float | None:
        raw = self.raw
        if raw is None:
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {"register": self.spec.tid}
