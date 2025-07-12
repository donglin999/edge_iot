import processApi from '@/services/processApi'

export default {
  namespaced: true,
  state: {
    processes: [],
    stats: {
      total_processes: 0,
      running_processes: 0,
      stopped_processes: 0,
      error_processes: 0,
      total_cpu_percent: 0,
      total_memory_mb: 0
    },
    loading: false,
    error: null
  },
  mutations: {
    SET_PROCESSES(state, processes) {
      state.processes = processes
    },
    SET_STATS(state, stats) {
      state.stats = stats
    },
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    UPDATE_PROCESS_STATUS(state, { processName, status }) {
      const process = state.processes.find(p => p.name === processName)
      if (process) {
        process.status = status
      }
    }
  },
  actions: {
    async fetchProcesses({ commit }) {
      try {
        commit('SET_LOADING', true)
        const response = await processApi.getProcesses()
        commit('SET_PROCESSES', response.processes)
        commit('SET_STATS', response.stats)
        commit('SET_ERROR', null)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching processes:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async startProcesses({ commit, dispatch }, processNames) {
      try {
        commit('SET_LOADING', true)
        await processApi.startProcesses(processNames)
        await dispatch('fetchProcesses')
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async stopProcesses({ commit, dispatch }, processNames) {
      try {
        commit('SET_LOADING', true)
        await processApi.stopProcesses(processNames)
        await dispatch('fetchProcesses')
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async restartProcesses({ commit, dispatch }, processNames) {
      try {
        commit('SET_LOADING', true)
        await processApi.restartProcesses(processNames)
        await dispatch('fetchProcesses')
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    updateProcessStatus({ commit }, payload) {
      commit('UPDATE_PROCESS_STATUS', payload)
    }
  },
  getters: {
    runningProcesses: state => state.processes.filter(p => p.status === 'running'),
    stoppedProcesses: state => state.processes.filter(p => p.status === 'stopped'),
    errorProcesses: state => state.processes.filter(p => p.status === 'error'),
    totalCpuUsage: state => state.stats.total_cpu_percent,
    totalMemoryUsage: state => state.stats.total_memory_mb
  }
}