import warnings

warnings.warn(
  "Fauna is decommissioning FQL v4. This driver is not compatible with FQL v10, "
  "the latest version. Fauna accounts created after August 21, 2024 must use "
  "FQL v10. Ensure you migrate existing projects to the official v10 driver by "
  "the v4 EOL date: https://github.com/fauna/fauna-python.",
  DeprecationWarning,
  stacklevel=2
)

__title__ = "FaunaDB"
__version__ = "4.5.2"
__api_version__ = "4"
__author__ = "Fauna, Inc"
__license__ = "MPL 2.0"
__copyright__ = "2023 Fauna, Inc"
