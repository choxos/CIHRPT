I want to create a comprehensive database of CIHR projects named CIHR Projects Tracker (CIHRPT). I have the data in JSON files in the cihr_projects_jsons folder. I want to create a website that displays the data in a comprehensive way.

This is not a standalone project. It is a part of the XeraDB project. We have different themes for different projects. But all of them are based on the same core. You can find the core in ~/Documents/GitHub/xeradb/shared_theme folder. Previously, I applied the theme to other two projects (OST and PRCT) and it worked well. You can find the OST project in ~/Documents/GitHub/OpenScienceTracker and PRCT in ~/Documents/GitHub/CitingRetracted folder. I especially like the PRCT project because it is a comprehensive database of retracted papers and is very beautiful and colorful.

In the shared_theme folder, you can find the specifics for the CIHRPT project in css/themes/cihrpt-theme.css. Now, I want to create the CIHRPT's web app like this:

1. First, assess all the files in the xeradb/shared_theme and OpenScienceTracker  and CitingRetracted folders to understand the structure and the logic.

2. After that, look at a couple of the JSON files in the cihr_projects_jsons folder to understand the data structure.

3. We also have a csv file that has other meta-data about the projects. Actually, it includes the exact things scrapped from the CIHR website. JSONs are made by Claude based on the title and abstract of the projects. Read both the JSONs and the csv file to understand the data structure.

4. Create the web app. You can have PRCT project as a reference of what parts the web app may need and how to incorporate beautiful parts. Please note that I want the PRCT project to be as colorful as the current one. But remain professional and minimalistic.

4. Commit the changes and push them to the remote repository.

5. Then, run it locally to make sure everything is working fine.

Let's GO!