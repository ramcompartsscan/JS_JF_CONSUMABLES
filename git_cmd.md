remember to share with vscode logged in user
clone
git status



git push -u origin main
git push

1. Stage the files
Run this command to add all untracked files (including the JS_JF_CONSUMABLES folder) to the staging area:
git add .

2. Commit the changes
Now that the files are staged, you can save them to your local history. Since the terminal output mentioned "Initial commit," we will use that as the message:
git commit -m "Initial commit"

3. Push to the remote repository
Finally, send your commit to the server (GitHub/GitLab/Bitbucket). Since you are on the master branch:
git push origin master