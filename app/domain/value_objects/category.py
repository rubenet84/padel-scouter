from enum import Enum


class PlayerCategory(Enum):
    INICIACION = "Iniciación"
    QUINTA     = "5ª Categoría"
    CUARTA     = "4ª Categoría"
    TERCERA    = "3ª Categoría"
    SEGUNDA    = "2ª Categoría"
    PRIMERA    = "1ª Categoría"
    PRO        = "Profesional"

    def weight(self) -> int:
        weights = {
            "Iniciación":   1,
            "5ª Categoría": 2,
            "4ª Categoría": 3,
            "3ª Categoría": 4,
            "2ª Categoría": 5,
            "1ª Categoría": 6,
            "Profesional":  7,
        }
        return weights[self.value]


class ScoringMethod(Enum):
    CON_VENTAJA = "con_ventaja"
    STAR_POINT  = "star_point"
    PUNTO_ORO   = "punto_oro"