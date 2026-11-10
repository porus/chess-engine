# Licensing

The project files are offered under the MIT License in the root `LICENSE` file. MIT is listed by the Open Source Initiative as an approved open-source license. It allows reuse, including commercial reuse, subject to preserving its notice and disclaimer.

An open-source license cannot require each user to ask for permission before reuse. If reuse must be approved individually, the code cannot be described as open source under the usual OSI definition. This repository uses MIT to meet the open-source requirement, so people can reuse the licensed files without consulting the author first.

The grant only applies to material the releaser has the right to license. Confirm ownership or redistribution rights for every included file before publishing. This archive omits the original `.git` directory and any source history.

## Dependencies and external engines

The tournament manager, chess engine, and tests use only the Python standard library. There is no vendored third-party code, engine binary, opening book, tablebase, or sample-game dataset. `THIRD_PARTY_NOTICES.md` is the place to record any future dependency or asset, including its version, source, license, and notices. Review transitive dependencies as well as direct ones.

The GitHub Actions workflow references `actions/checkout@v4` and `actions/setup-python@v5`; their upstream repositories publish MIT license files. Their source is fetched by the GitHub-hosted workflow and is not copied into this project. The local application does not install or run either action.

Stockfish is not included or invoked. Its official site says it is distributed under GPLv3. If it is added later, review the specific integration and distribution plan against GPLv3 before including or linking it; do not imply that the repository's MIT license covers Stockfish. This note is a project boundary, not a legal conclusion about a future design.

## References

- [OSI: MIT License](https://opensource.org/license/mit)
- [OSI: Open Source FAQ](https://opensource.org/faq)
- [Stockfish: About](https://stockfishchess.org/about/)
- [GNU General Public License version 3](https://www.gnu.org/licenses/gpl-3.0.en.html)
- [actions/checkout license](https://github.com/actions/checkout/blob/v4/LICENSE)
- [actions/setup-python license](https://github.com/actions/setup-python/blob/v5/LICENSE)
