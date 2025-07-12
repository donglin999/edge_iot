import WebSocketManager from '@/utils/websocket'

export default {
  namespaced: true,
  state: {
    connected: false,
    connecting: false,
    error: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    subscriptions: []
  },
  mutations: {
    SET_CONNECTED(state, connected) {
      state.connected = connected
    },
    SET_CONNECTING(state, connecting) {
      state.connecting = connecting
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    SET_RECONNECT_ATTEMPTS(state, attempts) {
      state.reconnectAttempts = attempts
    },
    ADD_SUBSCRIPTION(state, topic) {
      if (!state.subscriptions.includes(topic)) {
        state.subscriptions.push(topic)
      }
    },
    REMOVE_SUBSCRIPTION(state, topic) {
      state.subscriptions = state.subscriptions.filter(t => t !== topic)
    }
  },
  actions: {
    async connect({ commit, dispatch }) {
      try {
        commit('SET_CONNECTING', true)
        
        await WebSocketManager.connect()
        
        // Set up event handlers
        WebSocketManager.on('connected', () => {
          commit('SET_CONNECTED', true)
          commit('SET_CONNECTING', false)
          commit('SET_ERROR', null)
          commit('SET_RECONNECT_ATTEMPTS', 0)
          
          // Resubscribe to topics after reconnection
          dispatch('resubscribe')
        })
        
        WebSocketManager.on('disconnected', () => {
          commit('SET_CONNECTED', false)
          commit('SET_CONNECTING', false)
        })
        
        WebSocketManager.on('error', (error) => {
          commit('SET_ERROR', error)
          commit('SET_CONNECTING', false)
        })
        
        WebSocketManager.on('message', (message) => {
          dispatch('handleMessage', message)
        })
        
      } catch (error) {
        commit('SET_ERROR', error.message)
        commit('SET_CONNECTING', false)
      }
    },
    async disconnect({ commit }) {
      await WebSocketManager.disconnect()
      commit('SET_CONNECTED', false)
      commit('SET_CONNECTING', false)
    },
    async subscribe({ commit }, topic) {
      try {
        await WebSocketManager.subscribe(topic)
        commit('ADD_SUBSCRIPTION', topic)
      } catch (error) {
        commit('SET_ERROR', error.message)
      }
    },
    async unsubscribe({ commit }, topic) {
      try {
        await WebSocketManager.unsubscribe(topic)
        commit('REMOVE_SUBSCRIPTION', topic)
      } catch (error) {
        commit('SET_ERROR', error.message)
      }
    },
    async resubscribe({ state }) {
      for (const topic of state.subscriptions) {
        await WebSocketManager.subscribe(topic)
      }
    },
    handleMessage({ dispatch }, message) {
      switch (message.type) {
        case 'process_update':
          dispatch('processes/updateProcessStatus', message.data, { root: true })
          break
        case 'process_control':
          // Handle process control events
          break
        case 'data_update':
          dispatch('data/addRealtimeData', message.data, { root: true })
          break
        case 'system_status':
          // Handle system status updates
          break
        default:
          console.log('Unknown message type:', message.type)
      }
    }
  },
  getters: {
    isConnected: state => state.connected,
    isConnecting: state => state.connecting,
    connectionError: state => state.error,
    subscriptions: state => state.subscriptions
  }
}