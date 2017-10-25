# Item Catalog Project
This project is under the FSND.
A user can run this application to view the list of all the items present. But must be logged in to interact.
## Register application at google dev console
1. Go to google dev console
2. create a new project
3. on the credentials side generate credentials
4. fill the oauth consent screen details.
5. add authorized javascript origins, http://localhost:5000
6. save and download json
7. rename it to client_secrets.json and save it in catalog folder

## Steps to install and run
1. Clone the project.
2. Go to /catalog/static
3. Install the material components for web by the following command
-  npm install --save material-components-web
4. Go back to folder with vagrantfile.
5. Git bash there
6. vagrant up
7. vagrant ssh
9. cd /vagrant/catalog/
10. python app.py
11. The project is running at localhost:5000

### Google plus oauth2 is used.
### Developed using Flask in Python.
### Uses Material Components for Web by Google.
