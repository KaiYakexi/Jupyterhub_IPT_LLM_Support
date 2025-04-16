import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import {PageConfig} from '@jupyterlab/coreutils';

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'LLMWidgetExtensionManager:plugin',
  description: 'A JupyterLab extension that chooses which LLM Help extension to use.',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {

  async function getUserSupportGroup(): Promise<string> {

    let token = PageConfig.getToken();
    const UserSupportGroupEndpoint = '$JUPYTERHUB_URL/jupyterhub/services/askLLM/userSupportGroup';

    try{
      const response = await fetch(UserSupportGroupEndpoint, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`, 
            'Content-Type': 'application/json' },
      })
      if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.designatedSupportGroup
    } catch (error) {
      console.error('Failed to fetch support group:', error);
      return 'noSupport';
    }
  }
  
  
  (async () => {
    try {
      const supportGroup = await getUserSupportGroup();
      window.sessionStorage.setItem('UseExtension', supportGroup);
    } catch (error) {
      console.error('Error setting support group:', error);
      window.sessionStorage.setItem('UseExtension', 'noSupport');
    }
  })();
}
};

export default plugin;
