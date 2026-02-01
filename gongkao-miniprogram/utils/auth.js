const app = getApp();

// 检查登录状态
const checkLogin = () => {
  const token = wx.getStorageSync('token');
  return !!token;
};

// 微信登录
const wxLogin = () => {
  return new Promise((resolve, reject) => {
    wx.login({
      success: (res) => {
        if (res.code) {
          resolve(res.code);
        } else {
          reject(new Error('微信登录失败'));
        }
      },
      fail: reject
    });
  });
};

// 保存登录信息
const saveLoginInfo = (token, userInfo) => {
  wx.setStorageSync('token', token);
  wx.setStorageSync('userInfo', userInfo);
  app.globalData.token = token;
  app.globalData.userInfo = userInfo;
};

// 清除登录信息
const clearLoginInfo = () => {
  wx.removeStorageSync('token');
  wx.removeStorageSync('userInfo');
  app.globalData.token = null;
  app.globalData.userInfo = null;
};

// 获取用户信息
const getUserInfo = () => {
  return wx.getStorageSync('userInfo');
};

module.exports = {
  checkLogin,
  wxLogin,
  saveLoginInfo,
  clearLoginInfo,
  getUserInfo
};
