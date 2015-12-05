#!/bin/bash
# An ugly script to automate version bump + new zip file release.
# 1. Bump VERSION in nightscout_osx_menubar.py
# 2. Run

NEW_VERSION=`grep "VERSION = " nightscout_osx_menubar.py | grep -Eo '\d+\.\d+\.\d+'`
RELEASE_ZIP="nightscout-osx-menubar-$NEW_VERSION.zip"

echo "----- Previous release seems to be:"
echo "  `grep "Latest version" README.md | grep -Eo '\d+\.\d+\.\d+'` (README)"
echo "  `git tag --list | grep '^v' | sed 's/^v//' | tail -1` (git)"
echo "  `ls -1 release/nightscout-osx-menubar-*.zip | tail -1 | grep -Eo '\d+\.\d+\.\d+'` (file)"

echo "----- Creating release $NEW_VERSION"
read -r -p "Sounds good? [y/n] " response
if [[ $response =~ ^([yY][eE][sS]|[yY])$ ]]
then
  echo ""
  echo "----- Cleaning & building"
  rm -r build/ dist/
  python setup.py py2app >/dev/null

  echo ""
  echo "----- Zipping"
  rm -r release/*
  pushd dist/
  # The py2app output includes symlinks to system Python 2.7, which must remain intact
  zip --symlinks -r ../release/$RELEASE_ZIP . --exclude .DS_Store >/dev/null
  popd

  echo ""
  echo "----- Updating README"
  sed -i '' -e "s/Latest version: [0-9.]*/Latest version: $NEW_VERSION/g" README.md
  sed -i '' -e $(echo "s/nightscout-osx-menubar-[0-9.]*\.zip/"$RELEASE_ZIP"/g") README.md

  echo ""
  echo "----- Status:"
  git diff README.md
  git status

  echo ""
  echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  echo " Don't forget to tag the next commit with \"v"$NEW_VERSION"\":"
  echo ""
  echo "   git tag v"$NEW_VERSION"; git push origin --tags"
  echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  echo ""
fi
