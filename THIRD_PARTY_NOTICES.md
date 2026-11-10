# Third-party notices

No third-party source code, binary, chess data, media asset, or Python package dependency is distributed or required by this repository. The application and test suite use Python’s standard library only.

The optional GitHub Actions workflow calls `actions/checkout` v4 and `actions/setup-python` v5 on GitHub-hosted runners. Both upstream repositories publish MIT license files ([checkout v4](https://github.com/actions/checkout/blob/v4/LICENSE), [setup-python v5](https://github.com/actions/setup-python/blob/v5/LICENSE)). Their code is not copied into this repository or needed to run the application locally.

Before adding or bundling any dependency or asset, record its name, exact version, source URL, license identifier, copyright notice, and any required source-offer or attribution details here. Check transitive dependencies as well as direct dependencies. Do not treat this file as a substitute for checking the actual package and version being shipped.
