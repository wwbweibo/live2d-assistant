<template>
    <div class="setting-content">
        <v-tabs v-model="activeTab">
            <v-tab>模型设置</v-tab>
            <v-tab>助手设置</v-tab>
        </v-tabs>

        <v-tabs-items v-model="activeTab">
            <v-tab-item>
                <ModelSetting :onSetting />
            </v-tab-item>
            <v-tab-item>
                <div>助手设置内容</div>
            </v-tab-item>
        </v-tabs-items>
    </div>
</template>

<script>
import ModelSetting from './model_setting.vue'

export default {
    name: 'SettingModal',
    props: {
        onModelSettingChange: {
            type: Function,
            required: true
        },
        onAssistantSettingChange: {
            type: Function,
            required: true
        }
    },
    components: {
        ModelSetting
    },
    data() {
        return {
            activeTab: 0
        }
    }
}
</script>

<style scoped>
.settings-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 60px;
}
</style>