# package-template

> Template to quickly create a package for the SeSG ecossystem.

## How to use

### Cloning the repository

You can start by either cloning this repo with `git`, or, preferably, use `degit` to clone the repo without the git history.

To clone with `git`:

```sh
git clone git@github.com:sesgx/package-template.git
```

To clone with `degit`:

```sh
npx degit github:sesgx/package-template {package_name}
```

### Updating informations

Start with the `pyproject.toml` file. Update the following keys:

- `project.name`: Name of your package. Can include dashes (`-`)
- `project.description`: Description of your package. This description will be repeated in the `README.md` file, and also in the github project's description.
- `project.keywords`: Keywords of the repository.

If you intend on developing tests for the package, uncomment the `# TESTS-SECTION` section.

Now, open the `_README.md` (attention to the underscore). Update the following informations:

- First heading must be the name of the package.
- First quote must be the description of the package, same used in the `pyproject.toml` file.
- If provided, the usage section must include a code example on how to use the package.
- Testing section should exist only if the package includes testing.

Then, update the folder under `src/` to match the name of your package. Remember to replace dashes (`-`) with underscores (`_`).

At last, delete this file (`README.md`), and rename the `_README.md` file to `README.md`.