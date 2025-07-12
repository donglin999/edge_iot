<template>
  <div id="app">
    <el-config-provider :locale="locale">
      <router-view />
    </el-config-provider>
  </div>
</template>

<script>
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

export default {
  name: 'App',
  components: {
    ElConfigProvider
  },
  data() {
    return {
      locale: zhCn
    }
  },
  mounted() {
    // Initialize WebSocket connection
    this.$store.dispatch('websocket/connect')
    
    // Load initial data
    this.$store.dispatch('processes/fetchProcesses')
    this.$store.dispatch('data/fetchStats')
  },
  beforeUnmount() {
    // Close WebSocket connection
    this.$store.dispatch('websocket/disconnect')
  }
}
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  height: 100vh;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>