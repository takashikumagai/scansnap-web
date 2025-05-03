import json
import scansnap.utils 
import scansnap.websocketserver

class ScanEventListener(scansnap.utils.EventListenerBase):

    def on_state_changed(self,data):
        msg = json.dumps(data)
        print('MewScanEventListener.on_state_changed:',msg)
        scansnap.websocketserver.send_message_to_client(msg)

    def on_progress_updated(self,data):
        msg = json.dumps(data)
        print('MewScanEventListener.on_progress_updated:',msg)
        scansnap.websocketserver.send_message_to_client(msg)
