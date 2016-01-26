# Contributing to cappy

## Process for users with commit access

1. Someone makes an issue in the issue tracker.
This issue explains what feature is to be added or what bug is to be fixed.
The issue is automatically assigned a unique number

1. Another, possibly different, user creates a new branch for development regarding this issue.
 * The branch name is `XX-description-of-issue` where `XX` is the issue number and everything else is a brief description of the issue.
For example, the issue filed in which we stated the need for this contributing document was #4, so the branch was called `4-contributing`.

1. Development is done in the branch via a series of commits.

1. When the feature is nearly complete or the bug is fixed, a pull request on the feature branch is filed, usually by the user who did the work.
This notifies other users that some new code is ready for review.
Those users review the code by reading the changes and running the new tests.

1. Users may add more commits to address outstanding issues with the code.

1. Once someone thinks the code is in good shape, he/she comments "LGTM" (looks good to me).
This indicates to the user who made the request that it is ok to merge the feature branch into master.

1. **Rebase and squash:** Before merging we clean up the git history in two steps:
rebase the feature branch onto master so that the merge will be a fast-forward,
and squash the (potentially many) commits in the branch into fewer, more easily understood commits.
Fortunately, you can do both of these things at once from the command line:
  * `git checkout master` - switch to master branch
  * `git pull` - update master branch to remote
  * `git checkout XX-description-of-issue`
  * `git rebase -i master`. This opens up an editor with your commits listed at the top.
Changing a commit from "pick" to "squash" will cause that commit to be lumped in with the previous one.
You can re-order commits at this stage as well, which can be very useful for squasing e.g. non-consecutive whitespace commits together.
  * After this, you have the opportunity to write a new commit message for the combined commit. Use it to write a good, thorough commit message. Include the following elements
    * Description of changes
    * Reviewer(s)
    * Any issues fixed by the changes.
After the rebase, check to make sure all tests still pass.

1. Merge the feature branch into master
  * `git checkout XX-description-of-issue`
  * `git push origin XX-description-of-issue -f` -- Force push (`-f`) rebased to origin so GitHub automatically closes the pull request after merging to master.
  * `git checkout master`
  * `git merge --ff-only XX-description-of-issue` -- you should see "fast-forward" in the output. This will fail if a fast-forward merge is not possible, which probably indicates that something went wrong with rebasing.
  * `git push`
  * (Note: `git rebase` is a powerful command and this is only one aspect of it.
For an example of squashing, see [here](http://gitready.com/advanced/2009/02/10/squashing-commits-with-rebase.html).)

1. Delete the old branch.


### Branch naming

* Branches dealing with a specific issue should be called `XX-description` where `XX` is the issue's number and description is a description of the issue.
Note that branches may be worked on by more than one user.

* A special case exists for branches named `u/someUserName`.
These branches are for messing around.
You are allowed to rebase and force push to branches prefixed by `u/yourName`.
Other people work on your branches at their peril.
Use of personal branches for working on issues in the issue tracker is discouraged.


### Commits

* Commits should focus on precisely one feature or bug.
* Group whitespace changes to existing code into their own commits.
* It is allowed to make whitespace commits in feature branches not focused on whitespace (making separate branches for whitespace would be really annoying).

### Commit messages

Your commit message documents your changes for all time. Take pride in it. Commits should follow this format:

```
Brief one sentence description of the change, using the active present tense.
 
After one blank line, a paragraph describing the change in more detail, i.e.
giving context of the changes and how they influence code use, why it was
done this way, etc. For very small changes, this may not be needed if the
brief description captures the essence of the change.

Meta data about the commit, such as who reviewed it and what issues it fixes.
```
Example:

```
Refactor quizzwopper to handle doodliwigs
 
Quizzwopper was assuming that all inputs were gizmos, but needed
special handling to deal with doodliwigs, which have extra fuzzbinkle
attributes internally. The quizzwopper interface is unchanged and
existing code does not need to be changed.

Reviewed-by: MisterX
Fixes #42 
```

### Small Fixes

For small fixes, there is no need to open an issue.
The contributor must still create a new branch and make a PR for code review.

Examples of small fixes include:
 * Small whitespace or PEP8 fixes (that aren't related to existing feature branches).
 * Changing an error (or success) message to be more descriptive.
 * Updating docstrings.


## Dos

* **Do** Remove commented code before committing. Old code is in the version control history if you want to get it back. Until then commented out code just confuses the reader.
* **Do** use reversion commits to undo bad commits on master.
* **Do** add commits to master via merge.

## Do Nots

* **Do NOT** force push to master, ever.
* **Do not** push master until the changes are reviewed and approved.

