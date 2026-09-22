import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "ComfyUI.Qwen2_1_PE.DynamicImages",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Qwen2_1_PE_Rewrite") {
            // Save original methods
            const onConnectionsChange = nodeType.prototype.onConnectionsChange;
            const onNodeCreated = nodeType.prototype.onNodeCreated;

            // Define the dynamic inputs logic
            nodeType.prototype.updateImageInputs = function () {
                if (!this.inputs) return;
                
                // Find all inputs that start with 'image_'
                let imageInputs = [];
                for (let i = 0; i < this.inputs.length; i++) {
                    if (this.inputs[i].name.startsWith('image_')) {
                        imageInputs.push({ index: i, input: this.inputs[i] });
                    }
                }

                if (imageInputs.length === 0) return;

                // Sort by the number in 'image_X'
                imageInputs.sort((a, b) => {
                    let numA = parseInt(a.input.name.split('_')[1]);
                    let numB = parseInt(b.input.name.split('_')[1]);
                    return numA - numB;
                });

                // Get the last image input
                let lastInput = imageInputs[imageInputs.length - 1];

                // If the last input is connected, and we have less than 9, add a new one
                if (lastInput.input.link != null) {
                    if (imageInputs.length < 9) {
                        this.addInput("image_" + (imageInputs.length + 1), "IMAGE");
                    }
                } else {
                    // If the last input is NOT connected, check if there are multiple unconnected at the end
                    // Keep one empty socket at the end
                    while (imageInputs.length > 1) {
                        let last = imageInputs[imageInputs.length - 1];
                        let secondLast = imageInputs[imageInputs.length - 2];
                        
                        if (last.input.link == null && secondLast.input.link == null) {
                            this.removeInput(last.index);
                            imageInputs.pop();
                        } else {
                            break;
                        }
                    }
                }
            };

            // Inject into onNodeCreated
            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }
                
                if (!this.inputs) return;

                // When node is created, first hide all image inputs except image_1
                let imageInputs = [];
                for (let i = 0; i < this.inputs.length; i++) {
                    if (this.inputs[i].name.startsWith('image_')) {
                        imageInputs.push({ index: i, input: this.inputs[i] });
                    }
                }
                
                // Remove all unconnected inputs starting from the back, until only image_1 is left or an active link
                for (let i = imageInputs.length - 1; i > 0; i--) {
                    if (imageInputs[i].input.link == null && imageInputs[i-1].input.link == null) {
                        this.removeInput(imageInputs[i].index);
                    }
                }
                
                this.updateImageInputs();
            };

            // Inject into onConnectionsChange
            nodeType.prototype.onConnectionsChange = function (type, index, connected, link_info) {
                if (onConnectionsChange) {
                    onConnectionsChange.apply(this, arguments);
                }
                
                if (type === 1) { // 1 means Input changed
                    this.updateImageInputs();
                }
            };
        }
    }
});
