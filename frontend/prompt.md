I am building an AI workflow automation tool where users are able to drag and drop the nodes and edges to build an AI workflow.
THe main part of the workflow is tracking the input/output/configs required by the nodes. The current setup for this is in the file PropertiesPanel.jsx which is not so good. It has some issues like hardcoded configs and all. 

I want to build a modular PopertiesPanel component along with other modular component within it so the code is maintainable and production ready.
The current requirement is correctly displaying the inputs, configs and outputs in a proper JS object so that users see the simple schema. 
The backend sends the json_schema for input(also config within it) and output. To display this correctly. Use the below techstack:
npm install @jsonforms/core @jsonforms/react @jsonforms/material-renderers @mui/material @mui/icons-material @emotion/react @emotion/styled

Use the required things.