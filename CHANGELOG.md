## [0.5.2](https://github.com/teambge/bge-python-sdk/compare/v0.5.1...v0.5.2) (2023-07-12)


### Features

* **phenotype:** 新增写入表型数据的接口 ([a4421ec](https://github.com/teambge/bge-python-sdk/commit/a4421ec6cca9ce004ddb53d953e1a6357e82f442))
* **sms:** 新增发送短信接口 ([83c6823](https://github.com/teambge/bge-python-sdk/commit/83c682357bf34d68561dff78ad8c45c9475b5aff))



## [0.3.2](https://gitlab.omgut.com/bge/bge-python-sdk/compare/v0.2.4...v0.3.2) (2022-06-07)


### Bug Fixes

* 修复混淆代码打包错误的问题 ([592bc41](https://gitlab.omgut.com/bge/bge-python-sdk/commit/592bc4112a6ecc0c6c6b92036231fbbb22ba2274))
* 修复模型配置命令不输入模型编号无法进入下一步的问题 ([e942e02](https://gitlab.omgut.com/bge/bge-python-sdk/commit/e942e0271c25bb6cba5170c40ead5a6000702cf5))
* 专业级变异接口regions参数验证 ([56ab2c8](https://gitlab.omgut.com/bge/bge-python-sdk/commit/56ab2c812e6b7cf78534ba91884952081c57e3fb))
* regions参数改为列表传入 ([023554a](https://gitlab.omgut.com/bge/bge-python-sdk/commit/023554acdf471d45a9800753ab2f2e78addf5ed8))


### Features

* 更新 SDK 版本号至 v0.3.0 ([4cd68eb](https://gitlab.omgut.com/bge/bge-python-sdk/commit/4cd68eb6a85e33636934d73024133c948704df1b))
* 新增命令行打印输出命令运行时间戳 ([d9b2638](https://gitlab.omgut.com/bge/bge-python-sdk/commit/d9b263808748a5d57b3771d208bc6c7e53c9af39))
* 新增模型代码混淆功能至模型发布命令 ([1383072](https://gitlab.omgut.com/bge/bge-python-sdk/commit/13830724f0ecdbcc392a38ea7877a0a53c863c56))
* 新增专业级变异接口 ([b753be0](https://gitlab.omgut.com/bge/bge-python-sdk/commit/b753be0b57f86d3e74431cbee226430ff6113c5d))
* 增加模型代码混淆功能并使用 rich 增强命令行工具 ([44d83c6](https://gitlab.omgut.com/bge/bge-python-sdk/commit/44d83c6f71d6a3e511b5dc9f46790da2d9745ff8))
* **command:** 增加 bge config list 命令 ([be7e542](https://gitlab.omgut.com/bge/bge-python-sdk/commit/be7e5428efee38026f83acd1d2f33c94b9761c54))
* **model:** 新增模型本地服务器端口参数并在运行模型命令时尝试更新 docker 镜像 ([d408a1c](https://gitlab.omgut.com/bge/bge-python-sdk/commit/d408a1cc4c185b3fb2e8df645c270af207943080))


## [0.2.8](https://gitlab.omgut.com/bge/bge-python-sdk/compare/v0.2.4...v0.2.8) (2022-04-18)


### Bug Fixes

* 更新自定义命令顺序 ([df04fcb](https://gitlab.omgut.com/bge/bge-python-sdk/commit/df04fcb773f004f6a399bb1cedfaf3d2cfa9f546))
* 强制转 biosample_id 为大写,修复 get_taxon_abundance 返回 Model 对象 ([010d831](https://gitlab.omgut.com/bge/bge-python-sdk/commit/010d8313c997fcdb02de295373d8c5df08efcff1))
* 删除命令中 biosample_id 调用的 upper 方法 ([b43799d](https://gitlab.omgut.com/bge/bge-python-sdk/commit/b43799dccde09f39901d0fbe15f2ddb041cda707))
* 修复 py2 和 py3 对可变参数与关键字参数的位置格式问题 ([b9820b2](https://gitlab.omgut.com/bge/bge-python-sdk/commit/b9820b233e988b680eabd2ea77fbf4dba98476c7))
* 修复 python3.7 中 argparser 要求 add_subparsers 要明确指定 required 参数的问题 ([c5a7f32](https://gitlab.omgut.com/bge/bge-python-sdk/commit/c5a7f320ce9ec60baa65e6ed67259292b7b1cf51))
* 修复安装包时由于依赖造成包安装报错的问题 ([85f4625](https://gitlab.omgut.com/bge/bge-python-sdk/commit/85f462576dae64b696f4f8c95315cc2a98cf69bb))
* 修复参数为 None 时提示无 upper 的错误 ([8c78a2d](https://gitlab.omgut.com/bge/bge-python-sdk/commit/8c78a2d7e6e37b5146c3f3497862d972298aefc6))
* 修复模型配置命令不输入模型编号无法进入下一步的问题 ([e942e02](https://gitlab.omgut.com/bge/bge-python-sdk/commit/e942e0271c25bb6cba5170c40ead5a6000702cf5))
* 修改 get_user 方法默认使用 /profile 接口 ([0acde99](https://gitlab.omgut.com/bge/bge-python-sdk/commit/0acde99603c56b882916520d9c89786535f174e8))
* 专业级变异接口regions参数验证 ([56ab2c8](https://gitlab.omgut.com/bge/bge-python-sdk/commit/56ab2c812e6b7cf78534ba91884952081c57e3fb))
* regions参数改为列表传入 ([023554a](https://gitlab.omgut.com/bge/bge-python-sdk/commit/023554acdf471d45a9800753ab2f2e78addf5ed8))
* SDK命令行工具兼容windows系统，代码中print改为sys包输出 ([3cd2824](https://gitlab.omgut.com/bge/bge-python-sdk/commit/3cd2824013b12ccbffbcf24495beb57605044fe2))


### Features

* 新增专业级变异接口 ([b753be0](https://gitlab.omgut.com/bge/bge-python-sdk/commit/b753be0b57f86d3e74431cbee226430ff6113c5d))



## [0.1.5](https://gitlab.omgut.com/bge/bge-python-sdk/compare/v0.1.4...v0.1.5) (2021-09-22)


### Features

* 新增批量上传和目录上传接口和命令 ([d14033d](https://gitlab.omgut.com/bge/bge-python-sdk/commit/d14033d983661b304ebacd5a9adbabbd2c1db826))



## [0.1.4](https://gitlab.omgut.com/bge/bge-python-sdk/compare/v0.1.3...v0.1.4) (2021-09-18)


### Bug Fixes

* 更新单元测试 ([fe172c2](https://gitlab.omgut.com/bge/bge-python-sdk/commit/fe172c206f10c9fd85e32e26d2840572d7025f9b))
* 更新单元测试 OAuth2 的断言信息 ([bda033a](https://gitlab.omgut.com/bge/bge-python-sdk/commit/bda033af2f2c31c3006f6579bd2dfe708ee327e9))
* 更新日志输出 ([7e50abe](https://gitlab.omgut.com/bge/bge-python-sdk/commit/7e50abeab3dffd3dfe7b65b5bc96c4b1b56e0477))
* 模型文档预览工具逻辑修改 ([5ba6be5](https://gitlab.omgut.com/bge/bge-python-sdk/commit/5ba6be508242835b76a78b148d261d0de7905100))
* 删除 token 命令的 --save 参数 ([683a428](https://gitlab.omgut.com/bge/bge-python-sdk/commit/683a4283e5f45bae18ecce3d1fceb5d24ffdeb76))
* 删除无用参数 ([d7b4853](https://gitlab.omgut.com/bge/bge-python-sdk/commit/d7b4853849719a9bfe15ab026afd2542d38b32db))
* 删除test.py ([c7a8f80](https://gitlab.omgut.com/bge/bge-python-sdk/commit/c7a8f8017ebad9d5f87d8054fd31cc070f53d31f))
* 文档上传参数修改 ([59ceedc](https://gitlab.omgut.com/bge/bge-python-sdk/commit/59ceedc34808ebb325d1aa636498b9599e93e1cd))
* 修复 client.download 中下载文件时 timeout 参数未定义的问题 ([b363659](https://gitlab.omgut.com/bge/bge-python-sdk/commit/b36365975d21317ccfda65e95c5a0ccf75a9eb00))
* 修复 register_sample 返回对象时出错的问题 ([f848bb4](https://gitlab.omgut.com/bge/bge-python-sdk/commit/f848bb465957b7c8e29501cd2119d083024a5dba))
* 修复本地测试模型无法 print 打印输出的问题 ([5ee3eb8](https://gitlab.omgut.com/bge/bge-python-sdk/commit/5ee3eb8716ba42007cb032a7db45812f020d8166))
* 修复创建脚手架时未安装 requests_toolbelt 的问题 ([6f615d2](https://gitlab.omgut.com/bge/bge-python-sdk/commit/6f615d2bd697a5a3ffb71e6e3444a31da9d9084c))
* 修复命令行工具 bge config 运行中 endpoint 错误的问题 ([2ec09ef](https://gitlab.omgut.com/bge/bge-python-sdk/commit/2ec09efce433f646b816e3f0f3bb207de25ee9c0))
* 修复模型初始化包含字典的字典时出错的问题 ([83099ca](https://gitlab.omgut.com/bge/bge-python-sdk/commit/83099ca99332b8bbfac8b9c5abf1aa297c018203))
* 修复模型命令相关脚本中 docker 服务未启动时的错误提示问题 ([55a5045](https://gitlab.omgut.com/bge/bge-python-sdk/commit/55a5045e70218f54469a6e6578384c12c9718be9))
* 修复模型运行测试服务器时自动退出的问题 ([e851f22](https://gitlab.omgut.com/bge/bge-python-sdk/commit/e851f220b381fd4c0c53d2e8993847864fc22a12))
* 修复自定义异常类错误 ([eb56d51](https://gitlab.omgut.com/bge/bge-python-sdk/commit/eb56d51379c8881df349c37ca328a153ea3c09c2))
* 修改 bge model start 命令不存在 docker 镜像时自动拉取镜像 ([ff71129](https://gitlab.omgut.com/bge/bge-python-sdk/commit/ff711291b31efacaf274c4955778849c13ab5807))
* 修改 docker 服务未启动时的错误提示 ([6793b05](https://gitlab.omgut.com/bge/bge-python-sdk/commit/6793b05025cab458d1a0e83dcb94fce0cf151d11))
* 修改 timeout 参数 ([00bcdbb](https://gitlab.omgut.com/bge/bge-python-sdk/commit/00bcdbb0bbd480438615eac91a8d02801ce5e9b8))
* 修改版本号 ([e9d4ad2](https://gitlab.omgut.com/bge/bge-python-sdk/commit/e9d4ad243050ffbc70606c1581fbf04bdf001fde))
* 修改版本号 ([cb2e74d](https://gitlab.omgut.com/bge/bge-python-sdk/commit/cb2e74d5ecaa22d971b8202edd3d8a9574d8a726))
* 修改模型 main.py 模板 ([58f5b8b](https://gitlab.omgut.com/bge/bge-python-sdk/commit/58f5b8b77a88788cb930f859184273ff6b6e2e40))
* 修改模型依赖包安装命令 ([fcef9e4](https://gitlab.omgut.com/bge/bge-python-sdk/commit/fcef9e4134a112ced96e036954454d4f31a14e97))
* 修改判断是否已安装docker的逻辑 ([ac6c0af](https://gitlab.omgut.com/bge/bge-python-sdk/commit/ac6c0af9a5fdbaa2880c27439e17987186a3b50e))
* 修改为不指定具体依赖包版本 ([f67a7b6](https://gitlab.omgut.com/bge/bge-python-sdk/commit/f67a7b68825490597d5e9f459a971f230077b9a2))
* 直接使用 pytest，避免 tox 提示警告 make 为外部命令 ([1c025f1](https://gitlab.omgut.com/bge/bge-python-sdk/commit/1c025f1c6d6588946eeff1ecfdb48b61482abe56))


### Features

* 调整 API 初始化逻辑，去除 OAuth2 依赖 ([f0bbbfb](https://gitlab.omgut.com/bge/bge-python-sdk/commit/f0bbbfbab77b1478dc86c007403ceb7426f041d7))
* 调整初始化参数等，新增 alive 接口 ([a404ecf](https://gitlab.omgut.com/bge/bge-python-sdk/commit/a404ecf10acaef7a702e876474b443be5bdd285d))
* 更新版本号到 0.1.1 ([ed7746d](https://gitlab.omgut.com/bge/bge-python-sdk/commit/ed7746d01899990da9a3a82c5cce1e5d067a66f7))
* 更新模型相关命令 ([572bac4](https://gitlab.omgut.com/bge/bge-python-sdk/commit/572bac4a1bd88d2b7d16477d40d04d41e685a9e4))
* 获取变异位点与样品数据接口调整，去除问卷相关接口 ([99de9a2](https://gitlab.omgut.com/bge/bge-python-sdk/commit/99de9a2dcd8fadda5e6079b603b29ff2c60271ec))
* 模型文档发布命令 ([64ae8fa](https://gitlab.omgut.com/bge/bge-python-sdk/commit/64ae8fa4aa6374852efb409a08820101c2b5d97c))
* 模型文档上传接口 ([d1da6f4](https://gitlab.omgut.com/bge/bge-python-sdk/commit/d1da6f4a11cfea533742f9893121e662bdc1d297))
* 删除模型 build 命令并限制打包文件上传大小 ([97bc7fd](https://gitlab.omgut.com/bge/bge-python-sdk/commit/97bc7fd9c6ec6b9ff72073d78ab3ebd6cd8de3ca))
* 升级 SDK 命令行工具 ([5115e67](https://gitlab.omgut.com/bge/bge-python-sdk/commit/5115e67f2f8e1be45738309942bd184f2753b6a3))
* 升级版本号 ([071f0dd](https://gitlab.omgut.com/bge/bge-python-sdk/commit/071f0dde6237b6d386bcc954a5c10ac4eae99d1b))
* 添加git忽略文件 ([d1eb89f](https://gitlab.omgut.com/bge/bge-python-sdk/commit/d1eb89f19794511062aaf426fa414fda45b3f976))
* 项目重构 ([8e78015](https://gitlab.omgut.com/bge/bge-python-sdk/commit/8e78015776752757a1b3613220e367ed71ad6e9e))
* 项目重构 ([a088b39](https://gitlab.omgut.com/bge/bge-python-sdk/commit/a088b39d7e64fe622b1f4cfee28f04f340e88f94))
* 新增 api 命令行工具并重构命令实现方式 ([4d142b8](https://gitlab.omgut.com/bge/bge-python-sdk/commit/4d142b83dbf3cf9cfe99366f4ef07e48f58c68c0))
* 新增 OAuth2 数据模型，升级 Model 类，支持 json 格式的导入导出 ([740053a](https://gitlab.omgut.com/bge/bge-python-sdk/commit/740053a94dc03a6a205bb91cd8f9d39173db1363))
* 新增 sdk 打包 ignore 特性,支持定义不希望打包上传的 unix filename patterns ([08a8f46](https://gitlab.omgut.com/bge/bge-python-sdk/commit/08a8f46f9e8c290dd5713bb990aac31dac9e87e7))
* 新增 SDK 命令行工具 ([d8e8135](https://gitlab.omgut.com/bge/bge-python-sdk/commit/d8e813550a44f963c7a0db59937fefa65fa07d89))
* 新增 upload 方法直接上传文件 ([859f47a](https://gitlab.omgut.com/bge/bge-python-sdk/commit/859f47a2e63d990c97e62d6b5cff5c188ce73ec4))
* 新增客户端加密上传文件功能 ([c3a8983](https://gitlab.omgut.com/bge/bge-python-sdk/commit/c3a8983dfd1e416bd58af0378cbf35004c01d32b))
* 新增模型配置项可选菜单和整数范围限制 ([052dd54](https://gitlab.omgut.com/bge/bge-python-sdk/commit/052dd54d8426425ea22bd5307f7fdf51e295a5ef))
* 新增模型启动本地测试服务器命令 ([e11eda9](https://gitlab.omgut.com/bge/bge-python-sdk/commit/e11eda947c880d3ebba64a7156cadc4af0081b59))
* 新增上传 pypi 命令 ([b819ed0](https://gitlab.omgut.com/bge/bge-python-sdk/commit/b819ed078535616c4ddb42b4286d48ca7d587224))
* 新增上传模型数据集命令和接口，并增加文件上传进度日志 ([c987041](https://gitlab.omgut.com/bge/bge-python-sdk/commit/c9870410527e6da360aefd8a5026bf25bda93b05))
* 新增授权码模式、用户、任务等命令 ([d21c098](https://gitlab.omgut.com/bge/bge-python-sdk/commit/d21c098d831c4cb13d326994055aff8bccae2875))
* 新增数据流接口、部署模型、回滚模型接口 ([c78eed4](https://gitlab.omgut.com/bge/bge-python-sdk/commit/c78eed4eb98f7203ce7ff81bab35addfd4d703ea))
* 新增数据项接口 ([45b4e2f](https://gitlab.omgut.com/bge/bge-python-sdk/commit/45b4e2f64656a9f21b465f0a4db8ff00f73f82f7))
* 新增数据项接口 ([f91e7ea](https://gitlab.omgut.com/bge/bge-python-sdk/commit/f91e7eab95ce63396f76f124e480c98bdbc2ad3d))
* 新增文件上传默认增加自定义头部保存上传文件的客户端编号,并新增 introspect 接口 ([94947e2](https://gitlab.omgut.com/bge/bge-python-sdk/commit/94947e2e540fd7bfa1a3cd9b623cd48ff12d6b39))
* 新增下载文件到 file like object 的方法 ([30e74e7](https://gitlab.omgut.com/bge/bge-python-sdk/commit/30e74e7eaebb48686b3cbbce1d4fa1e25acbb2f8))
* 修改上传日志为单行覆盖输出 ([86a6e9f](https://gitlab.omgut.com/bge/bge-python-sdk/commit/86a6e9f7b0ba41c15f365c8b0971190e3627778f))
* 修改上传日志为单行覆盖输出 ([978af20](https://gitlab.omgut.com/bge/bge-python-sdk/commit/978af209bfb6ace017960ab696dbaf6ca07914c6))
* 异常捕获简化处理 ([bfff596](https://gitlab.omgut.com/bge/bge-python-sdk/commit/bfff596354e638b7a4f02c077468e770aa062cda))
* Change version ([af97b33](https://gitlab.omgut.com/bge/bge-python-sdk/commit/af97b33c14550696e4c5729494fc22d8908a2133))
* sdk第一次提交 ([77f7fa5](https://gitlab.omgut.com/bge/bge-python-sdk/commit/77f7fa503f071b0b316e5164b7a1e987264d6e83))



