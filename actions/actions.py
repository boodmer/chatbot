# Import the modules so their Action classes are registered
from .recommend import ActionRecommendBicycle   # noqa: F401
from .maintenance import ActionCheckMaintenanceStatus  # noqa: F401
from .categories import ActionShowCategoryDetail  # noqa: F401
from .orders import ActionCheckOrderStatus  # noqa: F401