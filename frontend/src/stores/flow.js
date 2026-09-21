import { defineStore } from "pinia";
import { ref } from "vue";

export const useFlowStore = defineStore("flow", () => {
  const caseId = ref(Number(sessionStorage.getItem("arbCaseId")) || 0);
  const scenarioId = ref(sessionStorage.getItem("arbScenarioId") || "");
  const scenarioTitle = ref(sessionStorage.getItem("arbScenarioTitle") || "");

  // 文书起草预置文件
  const presetFile = ref(null); // { url, type, name } - image 或 doc

  function setCase(payload) {
    caseId.value = payload.caseId;
    scenarioId.value = payload.scenarioId || "";
    scenarioTitle.value = payload.scenarioTitle || "";
    sessionStorage.setItem("arbCaseId", String(payload.caseId));
    sessionStorage.setItem("arbScenarioId", scenarioId.value);
    sessionStorage.setItem("arbScenarioTitle", scenarioTitle.value);
  }

  function clearCase() {
    caseId.value = 0;
    scenarioId.value = "";
    scenarioTitle.value = "";
    sessionStorage.removeItem("arbCaseId");
    sessionStorage.removeItem("arbScenarioId");
    sessionStorage.removeItem("arbScenarioTitle");
  }

  function setPresetFile(file) {
    presetFile.value = file;
    sessionStorage.setItem("arbPresetFile", JSON.stringify(file));
  }

  function clearPresetFile() {
    presetFile.value = null;
    sessionStorage.removeItem("arbPresetFile");
  }

  // 初始化时恢复预置文件
  const savedFile = sessionStorage.getItem("arbPresetFile");
  if (savedFile) {
    try {
      presetFile.value = JSON.parse(savedFile);
    } catch (e) {
      // ignore
    }
  }

  return { caseId, scenarioId, scenarioTitle, presetFile, setCase, clearCase, setPresetFile, clearPresetFile };
});
