import { createStore } from 'vuex'
import processes from './modules/processes'
import data from './modules/data'
import config from './modules/config'
import websocket from './modules/websocket'

export default createStore({
  modules: {
    processes,
    data,
    config,
    websocket
  },
  state: {
    loading: false,
    error: null
  },
  mutations: {
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    CLEAR_ERROR(state) {
      state.error = null
    }
  },
  actions: {
    setLoading({ commit }, loading) {
      commit('SET_LOADING', loading)
    },
    setError({ commit }, error) {
      commit('SET_ERROR', error)
    },
    clearError({ commit }) {
      commit('CLEAR_ERROR')
    }
  },
  getters: {
    isLoading: state => state.loading,
    error: state => state.error
  }
})