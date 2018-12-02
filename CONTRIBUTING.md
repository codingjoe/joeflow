# How to contribute

## Design Goals

### M.U.S.T

This package follows a couple of MUST have design principles.

##### Maintainable

The package and it is features needs to be maintainable. It is more important
upgrade to the latest Django or Python release than it is to add more
features.

##### User friendly

The features, as well as the code, should be accessible to users and first time
contributors. Documentation is key!

##### Specific

A good package solves only one problem and solves it well. We don't want people
to add code to their runtime environment that they don't need.

##### Tested

All features need to be tested. A CI suite should be in place. Running and
writing tests should be reasonably accessible for first time contributors.


## Release

We follow [semantic versioning](https://semver.org/). To release a new version
simply [create a new GitHub release][create-release], specify the version and
add the changelog into the release description.

[create-release]: https://github.com/codingjoe/joeflow/releases/new
