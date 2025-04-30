import {
  ILayoutRestorer,
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {CodeCellModel, isCodeCellModel} from '@jupyterlab/cells';
import {ICommandPalette, MainAreaWidget} from "@jupyterlab/apputils";
import {INotebookTracker, NotebookActions, NotebookPanel, NotebookTracker} from '@jupyterlab/notebook'
import {Widget} from '@lumino/widgets';
import {IOutput} from '@jupyterlab/nbformat'
import {PageConfig} from '@jupyterlab/coreutils';
import {IRenderMime, IRenderMimeRegistry, RenderMimeRegistry, standardRendererFactories} from "@jupyterlab/rendermime";

interface LLMResponse {
  LLMResponse: string;
}

class LLMResponseWidget extends Widget{
  private widgetContainer: HTMLElement;
  private _rendermime:IRenderMimeRegistry;
  private renderer:IRenderMime.IRenderer;
  constructor(rendermime: IRenderMimeRegistry) {
    super();
    this._rendermime= rendermime;
    this.addClass('LLM-responseWidget');
    this.widgetContainer = document.createElement('div');
    this.widgetContainer.classList.add('widget-container')
    //const introduction = document.createElement('p');
    //introduction.textContent = 'This is introductionary text, explaining the functionality of the service';
    //this.widgetContainer.appendChild(introduction);
    this.node.appendChild(this.widgetContainer);
    const errorContainer=document.createElement('div');
    errorContainer.classList.add('error-container');
    const errorHeader = document.createElement('div');
    errorHeader.classList.add('error-errorHeader');
    errorContainer.appendChild(errorHeader)
    this.renderer= this._rendermime.createRenderer('text/markdown');
    errorContainer.appendChild(this.renderer.node).classList.add('error-LLMDescription');
    this.widgetContainer.appendChild(errorContainer);
    
  }
  
  async updateWidget(execution_count:Number,cellIdentifier:any,error: IOutput,sourceCode: String): Promise<void>{
      const executionCounter=execution_count.toString()
      const traceback = error['traceback']?.toString()??'UndefinedErrorValue';
      const errorName = error['ename']?.toString()??'UndefinedErrorValue';
      const errorContainer= this.widgetContainer.querySelector('.error-container');
      const errorHeader= this.widgetContainer.querySelector('.error-errorHeader');
      if (errorHeader!=null){
        errorHeader.innerHTML=`<span class="error-number">Cell [${executionCounter}]</span> ${errorName}`;}
      if (errorContainer!=null){
      const model = this._rendermime.createModel({
        data: { 'text/markdown': "#Waiting for result..." }
      })
      this.renderer.renderModel(model);
      try {
        const data = await askLLM(executionCounter,cellIdentifier,errorName,traceback,sourceCode) as LLMResponse;
        const model = this._rendermime.createModel({
          data: { 'text/markdown': data['LLMResponse'] }
        });
        this.renderer.renderModel(model);
    } catch (er: unknown) {
        if (er instanceof Error){
          const model = this._rendermime.createModel({
            data: { 'text/markdown': "#Error getting result" }
          });
          this.renderer.renderModel(model);
      }
    }
      errorContainer.scrollIntoView({behavior:'smooth'});
    }

    async function askLLM(executionCounter:String, cellIdentifier:any,errorName:String, traceback:String,sourceCode:String): Promise<any> {
      let token = PageConfig.getToken();
      const HubLLMEndpoint = '$JUPYTERHUB_URL/jupyterhub/services/askLLM/errorLog';
      const requestData = {'supportType':'personalizedSupport','cellIdentifier':cellIdentifier,executionCounter: executionCounter,errorName:errorName,traceback:traceback,sourceCode:sourceCode};

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




  
  
  console.log('JupyterLab LLM development env extension is actives now Check');
  let widget: MainAreaWidget<LLMResponseWidget>;

  notebookTracker.currentChanged.connect(() => {
    const notebookPanel = notebookTracker.currentWidget;
    if (notebookPanel) {
      console.log('Current notebook:', notebookPanel);
    }
  });
  /* Tracker is not working right now, might not be necessay
  if I want it to work tho, I will probably have to serialize the widget */
  const command: string = 'personalizedSupport:open';
  app.commands.addCommand(command, {
    label: 'LLM Widget',
    execute: () => {
      if (!widget || widget.isDisposed) {
        setWidget()
      }
      if (!widget.isAttached) {
        // Attach the widget to the main work area if it's not there
        app.shell.add(widget, 'main',{ mode: 'split-right' });
      }
      // Activate the widget
      activateWidget()
        
      

  }});
  function setWidget(){
    const rendermime= new RenderMimeRegistry({
      initialFactories: standardRendererFactories
    });
    const content = new LLMResponseWidget(rendermime);
    widget = new MainAreaWidget({content});
    widget.id = 'LLMHelp-jupyterlab';
    widget.title.label = 'LLM Help';
    widget.title.closable = true;
  }
  function activateWidget(){
    app.shell.activateById(widget.id);
  }
  palette.addItem({ command, category: 'Tutorial' });


  NotebookActions.executed.connect((_, args) => {
    const { cell, success } = args;
    if (window.sessionStorage.getItem('UseExtension')=='personalizedSupport'){
    if (cell) {
      const cellModel = cell.model;
      if (isCodeCellModel(cellModel)){
        const cellIdentifier=cellModel.getMetadata('identifier')
        const cellJson = cell.model.toJSON();
        const sourceCode : String = String(cellJson.source);
        const execution_count=<Number>cellJson.execution_count;
        if (execution_count){
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
        if (!success) {
        if (!widget || widget.isDisposed){
          setWidget()
          activateWidget()
          app.shell.add(widget, 'main',{ mode: 'split-right' });
          }
          console.log('Error in Code, sending to LLM');
          widget.content.updateWidget(execution_count,cellIdentifier,errors[0],sourceCode);
        }
        if (success) {
          const output=JSON.stringify(outputArray);
          logSuccess(execution_count,cellIdentifier,output,sourceCode);
          console.log('Logging successful cell run');
        }
      }
    }
   } else {
      console.error('Cell is undefined or null.');
    }
  }});
  console.log('JupyterLab frontend extension testing is activated now!');
  console.log('ICommandPalette:',palette);

  async function logSuccess(execution_count:Number,cellIdentifier:any,outputArray:String,sourceCode:String): Promise<any>{
    let token = PageConfig.getToken();
    const successEndpoint = '$JUPYTERHUB_URL/jupyterhub/services/askLLM/successLog';
    const requestData = {'supportType':'personalizedSupport','cellIdentifier':cellIdentifier,executionCounter: execution_count,outputArray:outputArray,sourceCode:sourceCode};
    const response = await fetch(successEndpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`, 
        'Content-Type': 'application/json' },
      body: JSON.stringify({"requestData":requestData}),
  });
  if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
  }

}


 
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'LLMExtensionpersonalizedSupport:plugin',
  description: 'A JupyterLab LLM help extension.',
  autoStart: true,
  requires: [ICommandPalette, INotebookTracker],
  activate: activateWidget};
  

export default plugin;