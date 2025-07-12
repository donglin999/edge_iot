import configApi from '@/services/configApi'

export default {
  namespaced: true,
  state: {
    currentConfig: null,
    configHistory: [],
    uploadProgress: 0,
    validationResult: null,
    loading: false,
    error: null
  },
  mutations: {
    SET_CURRENT_CONFIG(state, config) {
      state.currentConfig = config
    },
    SET_CONFIG_HISTORY(state, history) {
      state.configHistory = history
    },
    SET_UPLOAD_PROGRESS(state, progress) {
      state.uploadProgress = progress
    },
    SET_VALIDATION_RESULT(state, result) {
      state.validationResult = result
    },
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    SET_ERROR(state, error) {
      state.error = error
    }
  },
  actions: {
    async fetchCurrentConfig({ commit }) {
      try {
        commit('SET_LOADING', true)
        const response = await configApi.getCurrentConfig()
        commit('SET_CURRENT_CONFIG', response)
        commit('SET_ERROR', null)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching current config:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async fetchConfigHistory({ commit }) {
      try {
        const response = await configApi.getConfigHistory()
        commit('SET_CONFIG_HISTORY', response.configs)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching config history:', error)
      }
    },
    async uploadConfig({ commit }, { file, description, applyImmediately }) {
      try {
        commit('SET_LOADING', true)
        commit('SET_UPLOAD_PROGRESS', 0)
        
        const response = await configApi.uploadConfig(file, description, applyImmediately, (progress) => {
          commit('SET_UPLOAD_PROGRESS', progress)
        })
        
        commit('SET_VALIDATION_RESULT', response.validation)
        commit('SET_ERROR', null)
        
        return response
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
        commit('SET_UPLOAD_PROGRESS', 0)
      }
    },
    async validateConfig({ commit }, configId) {
      try {
        commit('SET_LOADING', true)
        const response = await configApi.validateConfig(configId)
        commit('SET_VALIDATION_RESULT', response)
        commit('SET_ERROR', null)
        return response
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async applyConfig({ commit }, configApply) {
      try {
        commit('SET_LOADING', true)
        const response = await configApi.applyConfig(configApply)
        commit('SET_ERROR', null)
        return response
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    }
  },
  getters: {
    isValidConfig: state => state.validationResult?.is_valid || false,
    validationErrors: state => state.validationResult?.errors || [],
    validationWarnings: state => state.validationResult?.warnings || []
  }
}