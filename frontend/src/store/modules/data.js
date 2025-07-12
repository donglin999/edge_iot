import dataApi from '@/services/dataApi'

export default {
  namespaced: true,
  state: {
    realtimeData: [],
    historicalData: [],
    devices: [],
    measurements: [],
    stats: {
      total_devices: 0,
      active_devices: 0,
      total_measurements: 0,
      total_data_points: 0,
      data_rate_per_second: 0,
      storage_size_mb: 0,
      oldest_data: null,
      newest_data: null
    },
    loading: false,
    error: null
  },
  mutations: {
    SET_REALTIME_DATA(state, data) {
      state.realtimeData = data
    },
    SET_HISTORICAL_DATA(state, data) {
      state.historicalData = data
    },
    SET_DEVICES(state, devices) {
      state.devices = devices
    },
    SET_MEASUREMENTS(state, measurements) {
      state.measurements = measurements
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
    ADD_REALTIME_DATA(state, data) {
      state.realtimeData.push(...data)
      // Keep only last 1000 points
      if (state.realtimeData.length > 1000) {
        state.realtimeData = state.realtimeData.slice(-1000)
      }
    }
  },
  actions: {
    async fetchRealtimeData({ commit }, query) {
      try {
        commit('SET_LOADING', true)
        const response = await dataApi.getRealtimeData(query)
        commit('SET_REALTIME_DATA', response.data_points)
        commit('SET_ERROR', null)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching realtime data:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async fetchHistoricalData({ commit }, query) {
      try {
        commit('SET_LOADING', true)
        const response = await dataApi.getHistoricalData(query)
        commit('SET_HISTORICAL_DATA', response.data_points)
        commit('SET_ERROR', null)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching historical data:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async fetchDevices({ commit }) {
      try {
        const response = await dataApi.getDevices()
        commit('SET_DEVICES', response.devices)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching devices:', error)
      }
    },
    async fetchMeasurements({ commit }, deviceId) {
      try {
        const response = await dataApi.getMeasurements(deviceId)
        commit('SET_MEASUREMENTS', response.measurements)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching measurements:', error)
      }
    },
    async fetchStats({ commit }) {
      try {
        const response = await dataApi.getStatistics()
        commit('SET_STATS', response)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching stats:', error)
      }
    },
    addRealtimeData({ commit }, data) {
      commit('ADD_REALTIME_DATA', data)
    }
  },
  getters: {
    activeDevices: state => state.devices.filter(d => d.status === 'active'),
    latestDataPoint: state => state.realtimeData.length > 0 ? state.realtimeData[state.realtimeData.length - 1] : null,
    dataRate: state => state.stats.data_rate_per_second
  }
}