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
interface errorData {
  execution_count: String;
  traceback: String;
  errorName: String;
  sourceCode: String;
}

class LLMResponseWidget extends Widget{
  private widgetContainer: HTMLElement;
  private _rendermime:IRenderMimeRegistry;
  private renderer:IRenderMime.IRenderer;
  private errorContainer: HTMLElement;
  constructor(rendermime: IRenderMimeRegistry) {
    super();
    this._rendermime= rendermime;
    this.addClass('LLM-responseWidget');
    this.widgetContainer = document.createElement('div');
    this.widgetContainer.classList.add('widget-container')
    this.node.appendChild(this.widgetContainer);
    this.errorContainer=document.createElement('div');
    this.errorContainer.classList.add('error-container');
    this.renderer= this._rendermime.createRenderer('text/markdown');
    this.widgetContainer.appendChild(this.errorContainer);    
  }
  showPromptField(execution_count:Number,error: IOutput,sourceCode: String){
      this.clearPrompt()
      const executionCounter=execution_count.toString()
      const traceback = error['traceback']?.toString()??'UndefinedErrorValue';
      const errorName = error['ename']?.toString()??'UndefinedErrorValue';
      const errorData={execution_count:executionCounter,traceback:traceback,errorName:errorName,sourceCode:sourceCode} as errorData;
      console.log(errorData);
      const promptContainer= document.createElement('div');
      promptContainer.classList.add('prompt-container');
      const inputField = document.createElement('textarea');
      inputField.classList.add('promptInput');
      inputField.placeholder = 'Write your own prompt to ask the large language model...';
      const inputButton = document.createElement('button');
      inputButton.textContent='Send Prompt to LLM';
      promptContainer.appendChild(inputField);
      promptContainer.appendChild(inputButton);
      this.errorContainer.appendChild(promptContainer);
      inputButton.addEventListener('click', () => {
        const prompt=inputField.value;
        this.updateWidget(errorData,prompt)});

    }

  clearPrompt() {
    const promptContainer = this.errorContainer.querySelector('.prompt-container');
    if (promptContainer){
      this.errorContainer.removeChild(promptContainer);
    }
    const newSelector = this.errorContainer.querySelector('.error-errorHeader');
    const selectorTwo = this.errorContainer.querySelector('.error-LLMDescription');
    if (newSelector){
      this.errorContainer.removeChild(newSelector);
    }
    if (selectorTwo){
      this.errorContainer.removeChild(selectorTwo);
    }
  }
  
  async updateWidget(errorData: errorData, prompt:String): Promise<void>{
      this.clearPrompt();
      const errorHeader = document.createElement('div');
      errorHeader.classList.add('error-errorHeader');
      this.errorContainer.appendChild(errorHeader);
      this.errorContainer.appendChild(this.renderer.node).classList.add('error-LLMDescription');
      if (errorHeader!=null){
        errorHeader.innerHTML=`<span class="error-number">Cell [${errorData['execution_count']}]</span> ${errorData['errorName']}`;}
      if (this.errorContainer!=null){
        console.log(this.errorContainer);
      const model = this._rendermime.createModel({
        data: { 'text/markdown': "#Waiting for result..." }
      })
      this.renderer.renderModel(model);
      try {
        const data = await askLLM(errorData['execution_count'],errorData['errorName'],errorData['traceback'],errorData['sourceCode'],prompt) as LLMResponse;
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
      this.errorContainer.scrollIntoView({behavior:'smooth'});
    }

    async function askLLM(executionCounter:String, errorName:String, traceback:String,sourceCode:String,prompt:String): Promise<any> {
      let token = PageConfig.getToken();
      const HubLLMEndpoint = 'http://localhost:8533/jupyterhub/services/askLLM/errorLog';
      const requestData = {"supportType":"customPrompt",executionCounter: executionCounter,errorName:errorName,traceback:traceback,sourceCode:sourceCode,"customPrompt":prompt};

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

  /* Tracker is not working right now, might not be necessay
  if I want it to work tho, I will probably have to serialize the widget */
  const command: string = 'customSupport:open';
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
    const { cell, success, error, notebook} = args;
    console.log(error,notebook);
    const test= cell.model;
    console.log(test.metadata)
    if (window.sessionStorage.getItem('UseExtension')=='customPrompt'){
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
        if (!widget || widget.isDisposed){
          setWidget()
          activateWidget()
          app.shell.add(widget, 'main',{ mode: 'split-right' });
          }
          console.log('Error in Code, sending to LLM');
          logFailure(execution_count,errors[0],sourceCode);
          widget.content.showPromptField(execution_count,errors[0],sourceCode);
        }
        if (success) {
          const output=JSON.stringify(outputArray);
          logSuccess(execution_count,output,sourceCode);
          console.log('Logging successful cell run');
        }
      }
    } else {
      console.error('Cell is undefined or null.');
    }
  }});
  console.log('JupyterLab frontend extension testing is activated now!');
  console.log('ICommandPalette:',palette);

  async function logSuccess(execution_count:Number, outputArray:String,sourceCode:String): Promise<any>{
    let token = PageConfig.getToken();
    const successEndpoint = 'http://localhost:8533/jupyterhub/services/askLLM/successLog';
    const requestData = {supportType:"customPrompt",executionCounter: execution_count,outputArray:outputArray,sourceCode:sourceCode};
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
  async function logFailure(execution_count:Number,error: IOutput,sourceCode: String): Promise<any>{
    const executionCounter=execution_count.toString()
    const traceback = error['traceback']?.toString()??'UndefinedErrorValue';
    const errorName = error['ename']?.toString()??'UndefinedErrorValue';
    let token = PageConfig.getToken();
    const successEndpoint = 'http://localhost:8533/jupyterhub/services/askLLM/failureLog';
    const requestData = {"supportType":"customPrompt",executionCounter: executionCounter,errorName:errorName,traceback:traceback,sourceCode:sourceCode};
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
  id: 'LLMExtensionCustomPrompt:plugin',
  description: 'A JupyterLab LLM help extension.',
  autoStart: true,
  requires: [ICommandPalette, INotebookTracker],
  activate: activateWidget};
  

export default plugin;