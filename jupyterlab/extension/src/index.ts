import {
  ILayoutRestorer,
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {CodeCellModel, isCodeCellModel} from '@jupyterlab/cells';
import {ICommandPalette, MainAreaWidget, WidgetTracker} from "@jupyterlab/apputils";
import {INotebookTracker, NotebookActions, NotebookPanel, NotebookTracker} from '@jupyterlab/notebook'
import {Widget} from '@lumino/widgets';
import {IOutput} from '@jupyterlab/nbformat'
import {PageConfig} from '@jupyterlab/coreutils';


interface LLMResponse {
  LLMResponse: string;
}

class LLMResponseWidget extends Widget{
  private widgetContainer: HTMLElement;
  constructor() {
    super();

    this.addClass('LLM-responseWidget');
    this.widgetContainer = document.createElement('div');
    this.widgetContainer.classList.add('widget-container')
    const introduction = document.createElement('p');
    introduction.textContent = 'This is introductionary text, explaining the functionality of the service';
    this.widgetContainer.appendChild(introduction);
    this.node.appendChild(this.widgetContainer);
  }
  private createErrorContainer(execution_count:Number,error: IOutput): HTMLElement{
    const errorContainer= document.createElement('div');
    errorContainer.classList.add('error-container');

    const errorHeader = document.createElement('div');
    errorHeader.classList.add('error-errorHeader');
    const errorName = error['ename']?.toString()?? 'UndefinedErrorValue';
    const executionCounter=execution_count.toString()
    errorHeader.innerHTML=`<span class="error-number">[${executionCounter}]</span> ${errorName}`;
    
    const errorBox = document.createElement('div');
    errorBox.classList.add('error-box');
    const traceback = error['traceback']?.toString()??'UndefinedErrorValue';
    errorBox.textContent = traceback;
    
    const LLMDescription = document.createElement('div');
    LLMDescription.classList.add('error-LLMDescription');
    LLMDescription.textContent='Waiting for result...';
    errorContainer.appendChild(errorHeader);
    errorContainer.appendChild(errorBox);
    errorContainer.appendChild(LLMDescription);

     return errorContainer;
  }
  async logSuccess(execution_count:Number, outputArray:String,sourceCode:String): Promise<any>{
    let token = PageConfig.getToken();
    const logEndpoint = 'http://127.0.0.1:8000/services/askLLM/successLog';
    const requestData = {executionCounter: execution_count,outputArray:outputArray,sourceCode:sourceCode};
    const response = await fetch(logEndpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`, 
        'Content-Type': 'application/json' },
      body: JSON.stringify(requestData),
  });
  if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
  }
  async addLLMResult(execution_count:Number,errors: IOutput[],sourceCode: String): Promise<void>{
    for (const error of errors){;
      const errorContainer = this.createErrorContainer(execution_count, error);
      this.widgetContainer.appendChild(errorContainer);

      const executionCounter=execution_count.toString()
      const traceback = error['traceback']?.toString()??'UndefinedErrorValue';
      const errorName = error['ename']?.toString()?? 'UndefinedErrorValue';
      const LLMDescription = errorContainer.querySelector('.error-LLMDescription')!;
      try {
        const data = await askLLM(executionCounter,errorName,traceback,sourceCode) as LLMResponse;
        LLMDescription.textContent= `Result: ${data['LLMResponse']}`;
    } catch (er: unknown) {
        if (er instanceof Error){
        LLMDescription.textContent=`Error: ${er.message}`;
      }
    }
      errorContainer.scrollIntoView({behavior:'smooth'});
    }

    async function askLLM(executionCounter:String, errorName:String, traceback:String,sourceCode:String): Promise<any> {
      let token = PageConfig.getToken();
      const HubLLMEndpoint = 'http://127.0.0.1:8000/services/askLLM/';
      const requestData = {executionCounter: executionCounter,errorName:errorName,traceback:traceback,sourceCode:sourceCode};

      const response = await fetch(HubLLMEndpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`, 
          'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }
    }
  };

function activateWidget(app: JupyterFrontEnd, palette: ICommandPalette, notebookTracker: NotebookTracker, notebookPanel:NotebookPanel, restorer:ILayoutRestorer){
  
  console.log('JupyterLab LLM extension is active');
  let widget: MainAreaWidget<LLMResponseWidget>;

  /* Tracker is not working right now, might not be necessay
  if I want it to work tho, I will probably have to serialize the widget */
  const command: string = 'LLMWidget:open';
  app.commands.addCommand(command, {
    label: 'LLM Widget',
    execute: () => {
      if (!widget || widget.isDisposed) {
        const content = new LLMResponseWidget();
        widget = new MainAreaWidget({content});
        widget.id = 'LLMHelp-jupyterlab';
        widget.title.label = 'LLM Help';
        widget.title.closable = true;
      }
      if (!tracker.has(widget)) {
        // Track the state of the widget for later restoration
        tracker.add(widget);
      }
      if (!widget.isAttached) {
        // Attach the widget to the main work area if it's not there
        app.shell.add(widget, 'main');
      }
      // Activate the widget
      app.shell.activateById(widget.id);
    }
  });

  // Add the command to the palette.
  palette.addItem({ command, category: 'Tutorial' });

  // Track and restore the widget state => Needs serialization function, if I want to add it.

  let tracker = new WidgetTracker<MainAreaWidget<LLMResponseWidget>>({
    namespace: 'LLMWidget'
  });
  if (restorer) {
    restorer.restore(tracker, {
      command,
      name: () => 'LLMWidget'
    });
  }
  NotebookActions.executed.connect((_, args) => {
    const { cell, success } = args;
    if (cell) {
      const cellModel = cell.model;
      if (isCodeCellModel(cellModel)){
        const cellJson = cell.model.toJSON();
        const sourceCode : String = String(cellJson.source);
        const execution_count=<Number>cellJson.execution_count;
        const outputCast = <CodeCellModel>cell.model;
        const outputs = outputCast.sharedModel.outputs;
        let outputArray=[];
        let errors: IOutput[] =[];
        for (let i=0;i<outputs.length;i++){
          if (outputs[i]['output_type']==='error'){
            errors.push(outputs[i]);
           }
          else {
             outputArray.push(outputs[i]['text']);}
        }
         if (outputArray.length>0){
          console.log('Output Saved as'+JSON.stringify(outputArray));
          console.log('Source'+sourceCode);
          console.log('Output'+outputArray);
        }
        if (!success) {
          console.log('Error in Code, sending to LLM');
          widget.content.addLLMResult(execution_count,errors,sourceCode);
        }
        if (success) {
          const output=JSON.stringify(outputArray);
          widget.content.logSuccess(execution_count,output,sourceCode);
          console.log('Logging successful cell run');
        }
      }
    } else {
      console.error('Cell is undefined or null.');
    }
  });
  console.log('JupyterLab frontend extension testing is activated!');
  console.log('ICommandPalette:',palette);
}



const plugin: JupyterFrontEndPlugin<void> = {
  id: 'myextension:plugin',
  description: 'A JupyterLab extension.',
  autoStart: true,
  requires: [ICommandPalette, INotebookTracker],
  activate: activateWidget};
  

export default plugin;