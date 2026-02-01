App({
  globalData: {
    userInfo: null,
    token: null,
    baseUrl: 'https://shxtj.chaim.top/api/v1'
  },
  
  onLaunch: function() {
    console.log('小程序启动');
    // 检查登录状态
    try {
      const token = wx.getStorageSync('token');
      if (token) {
        this.globalData.token = token;
        console.log('已有登录Token');
      }
    } catch (e) {
      console.error('启动错误:', e);
    }
  }
});
