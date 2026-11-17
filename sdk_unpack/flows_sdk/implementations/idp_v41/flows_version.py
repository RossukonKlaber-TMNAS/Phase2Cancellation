# This constant determines the version of the flows that will be generated if not present.
# This should not necessarily match the current platform version.
# It should only be set to the current version before releasing major or minor versions
# that should come with new out-of-the-box flows.
# Format: "V<major>_<minor>". If we target major version, we skip the underscore and minor.
FLOWS_VERSION = 'V41'

# This constant is used in the out-of-the-box flows' titles and is computed from FLOWS_VERSION.
FLOWS_VERSION_DOTTED = FLOWS_VERSION.replace('_', '.')
