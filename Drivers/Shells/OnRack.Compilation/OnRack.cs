//------------------------------------------------------------------------------
// <auto-generated>
//     This code was generated by TestShell Driver Builder Version 6.4.0.
//
//     Changes to this file may cause incorrect behavior and will be lost if
//     the code is regenerated.
// </auto-generated>
//------------------------------------------------------------------------------

#define TRACE
using System;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Reflection;
using System.Diagnostics;
using System.Security.Permissions;
using System.Runtime.Remoting.Messaging;
using System.Runtime.Remoting;
using System.Runtime.Remoting.Proxies;
using System.Collections.Generic;
using System.ComponentModel;
using Microsoft.Win32;
using QualiSystems.Libraries;
using QualiSystems.Driver;

[assembly: AssemblyVersion("1.0.1259.14344")]
[assembly: AssemblyFileVersion("1.0.1259.14344")]
[assembly: AssemblyTitle("A project for creating a service driver.\r\nThese drivers can be attached to services and used to execute the driver commands.\r\nService drivers are useful for exposing automation to end users.")]
[assembly: AssemblyProduct("[<AssemblyName>] 6.4.0")]
[assembly: Library(typeof(onrack), "", IsolationLevel.PerLibrary)]




namespace QualiSystems.Driver
{
	[Description("A project for creating a service driver.\r\nThese drivers can be attached to services and used to execute the driver commands.\r\nService drivers are useful for exposing automation to end users.")]
    public class onrack : ICancelable, IDisposable
    {
        private static readonly Assembly DriverRuntimeAssembly;
        private static readonly string DriverRuntimeTypeName;
        private static readonly string DriverCodeBase;
		private Guid m_DriverIdentifier;
        
		private IFunctionInterpreter m_DeployESXsFunctionInterpreter = null;
		private object m_DeployESXsFunctionInterpreterLock = new object();
		private IFunctionInterpreter m_PopulateResourcesFunctionInterpreter = null;
		private object m_PopulateResourcesFunctionInterpreterLock = new object();
		private IFunctionInterpreter m_EndSessionFunctionInterpreter = null;
		private object m_EndSessionFunctionInterpreterLock = new object();
		private IFunctionInterpreter m_InitFunctionInterpreter = null;
		private object m_InitFunctionInterpreterLock = new object();
		private IFunctionInterpreter m_ResetDriverFunctionInterpreter = null;
		private object m_ResetDriverFunctionInterpreterLock = new object();
		private IFunctionInterpreter m_DeployESXFunctionInterpreter = null;
		private object m_DeployESXFunctionInterpreterLock = new object();
		private IFunctionInterpreter m_GetTasksFunctionInterpreter = null;
		private object m_GetTasksFunctionInterpreterLock = new object();
		private IFunctionInterpreter m_GetTaskStatusFunctionInterpreter = null;
		private object m_GetTaskStatusFunctionInterpreterLock = new object();
		private IFunctionInterpreter m_PopulateSystemFunctionInterpreter = null;
		private object m_PopulateSystemFunctionInterpreterLock = new object();
		private IFunctionInterpreter m_WaitForTaskFunctionInterpreter = null;
		private object m_WaitForTaskFunctionInterpreterLock = new object();

		
		static onrack()
		{
			DriverCodeBase = Assembly.GetExecutingAssembly().CodeBase;
			TestShellRuntimeLocator runtimeLocator = new TestShellRuntimeLocator("6.4.0");
            DriverRuntimeAssembly = runtimeLocator.RuntimeAssembly;
            DriverRuntimeTypeName = runtimeLocator.RuntimeTypeName;
		}
		
		private void __Shutdown() 
		{
			Type runtimeType = DriverRuntimeAssembly.GetType(DriverRuntimeTypeName);
			runtimeType.GetMethod("Shutdown").Invoke(null, BindingFlags.Public | BindingFlags.Static, null, new object[0], null);
		}

        public onrack()
        {
			m_DriverIdentifier = Guid.NewGuid();

			Type runtimeType = DriverRuntimeAssembly.GetType(DriverRuntimeTypeName);
			bool IsSupportedVersion = (bool)runtimeType.GetMethod("IsSupportedRuntimeVersion").Invoke(null, new object[]{"6.4.0"});
			if (!IsSupportedVersion)
				throw TestShellRuntimeLocator.NoMatchingRuntimeException("6.4.0");

			runtimeType.GetMethod("InitializeRuntime").Invoke(null, new object[]{Assembly.GetExecutingAssembly().CodeBase, "onrack", m_DriverIdentifier.ToString()});
                      
			m_DeployESXsFunctionInterpreter = CreateFunctionInterpreter("onrack\\Commands\\DeployESXs.tsdrv");
			m_PopulateResourcesFunctionInterpreter = CreateFunctionInterpreter("onrack\\Commands\\PopulateResources.tsdrv");
			m_EndSessionFunctionInterpreter = CreateFunctionInterpreter("onrack\\Initialization\\EndSession.tsdrv");
			m_InitFunctionInterpreter = CreateFunctionInterpreter("onrack\\Initialization\\Init.tsdrv");
			m_ResetDriverFunctionInterpreter = CreateFunctionInterpreter("onrack\\Initialization\\ResetDriver.tsdrv");
			m_DeployESXFunctionInterpreter = CreateFunctionInterpreter("onrack\\OnRack Functions\\DeployESX.tsdrv");
			m_GetTasksFunctionInterpreter = CreateFunctionInterpreter("onrack\\OnRack Functions\\GetTasks.tsdrv");
			m_GetTaskStatusFunctionInterpreter = CreateFunctionInterpreter("onrack\\OnRack Functions\\GetTaskStatus.tsdrv");
			m_PopulateSystemFunctionInterpreter = CreateFunctionInterpreter("onrack\\OnRack Functions\\PopulateSystem.tsdrv");
			m_WaitForTaskFunctionInterpreter = CreateFunctionInterpreter("onrack\\OnRack Functions\\WaitForTask.tsdrv");

        }
        

        
		[Hidden]
		public CancellationContext CreateCancellationContext()
		{
			return new CancellationContext();
		}

		[Hidden]
		public bool Cancel(CancellationContext cancellationContext)
		{
			Type runtimeType = DriverRuntimeAssembly.GetType(DriverRuntimeTypeName);
			return (bool)runtimeType.GetMethod("Cancel").Invoke(null, new object[]{cancellationContext.CallId});
		}

		[Hidden]
		public void Dispose()
		{
			Type runtimeType = DriverRuntimeAssembly.GetType(DriverRuntimeTypeName);
			runtimeType.GetMethod("DisposeDriverInstance").Invoke(null, new object[]{m_DriverIdentifier.ToString()});
		}

        private IFunctionInterpreter CreateFunctionInterpreter(string functionVirtualPath)
        {
            return new DucktypingProxy<IFunctionInterpreter>(DriverRuntimeAssembly.CreateInstance(
                    DriverRuntimeTypeName, false, BindingFlags.Default, null, new object[] { m_DriverIdentifier.ToString(), functionVirtualPath }, null, null)).TransparentProxy;
        }

		[Alias("Deploy ESXs")]
		[Folder("Commands")]
		[Cancelable]
		public void @DeployESXs([Description("A predefined matrix with the following columns: attribute, mandatory / optional (empty is mandatory), value - this column will be automatically populated when executing the command.")][Alias("resource")][ParameterDefaultValue("{['ResourceName','','';'ResourceFullName','','';'ResourceFamily','','';'ResourceModel','','';'ResourceDescription','','';'ESX Gateway','','';'ESX Domain','','';'ESX DNS1','','';'ESX DNS2','','';'ESX Root Password','','';'OnRack Address','','';'OnRack Username','','';'OnRack Password','','';'DeployTable','','']}")]  string[,] @resource, [Alias("out")] out string @out, [Description("A predefined matrix with the following columns: attribute, mandatory / optional (empty is mandatory), value - this column will be automatically populated when executing the command.")][Alias("reservation")][ParameterDefaultValue("{['Username','','';'Password','','';'Domain','','';'ReservationId','','']}")]  string[,] @reservation, [Description("List of connectors that are connected to the resource")][Alias("connectors")][ParameterDefaultValue("{['Index','Source','Target','Direction','Alias';]}")]  string[,] @connectors, [Description("List of attributes for the connectors")][Alias("connectorsAttributes")][ParameterDefaultValue("{['ConnectorIndex','Name','Value';]}")]  string[,] @connectorsAttributes)
		{
			lock(m_DeployESXsFunctionInterpreterLock)
			{
				if(m_DeployESXsFunctionInterpreter == null)
					m_DeployESXsFunctionInterpreter = CreateFunctionInterpreter("onrack\\Commands\\DeployESXs.tsdrv");
			}
			Guid callId = Guid.Empty;
			if(CancellationContext.Current != null)
				callId = CancellationContext.Current.CallId;
			Dictionary<string, object> inputNamesValues = new Dictionary<string, object>();
			inputNamesValues["resource"] = @resource;
			inputNamesValues["reservation"] = @reservation;
			inputNamesValues["connectors"] = @connectors;
			inputNamesValues["connectorsAttributes"] = @connectorsAttributes;
			Dictionary<string, Type> outputNamesTypes = new Dictionary<string, Type>();
			outputNamesTypes["out"] = typeof(string);
			Dictionary<string, object> outputNamesValues = m_DeployESXsFunctionInterpreter.Run(callId, inputNamesValues, outputNamesTypes);
			@out =  (string)outputNamesValues["out"];
		}

		[Alias("Populate Resources")]
		[Folder("Commands")]
		[Cancelable]
		public void @PopulateResources([Description("A predefined matrix with the following columns: attribute, mandatory / optional (empty is mandatory), value - this column will be automatically populated when executing the command.")][Alias("resource")][ParameterDefaultValue("{['ResourceName','','';'ResourceFullName','','';'ResourceFamily','','';'ResourceModel','','';'ResourceDescription','','';'OnRack Address','','';'OnRack Username','','';'OnRack Password','','']}")]  string[,] @resource, [Alias("out")] out string @out, [Description("A predefined matrix with the following columns: attribute, mandatory / optional (empty is mandatory), value - this column will be automatically populated when executing the command.")][Alias("reservation")][ParameterDefaultValue("{['Username','','';'Password','','';'Domain','','';'ReservationId','','']}")]  string[,] @reservation, [Description("List of connectors that are connected to the resource")][Alias("connectors")][ParameterDefaultValue("{['Index','Source','Target','Direction','Alias';]}")]  string[,] @connectors, [Description("List of attributes for the connectors")][Alias("connectorsAttributes")][ParameterDefaultValue("{['ConnectorIndex','Name','Value';]}")]  string[,] @connectorsAttributes)
		{
			lock(m_PopulateResourcesFunctionInterpreterLock)
			{
				if(m_PopulateResourcesFunctionInterpreter == null)
					m_PopulateResourcesFunctionInterpreter = CreateFunctionInterpreter("onrack\\Commands\\PopulateResources.tsdrv");
			}
			Guid callId = Guid.Empty;
			if(CancellationContext.Current != null)
				callId = CancellationContext.Current.CallId;
			Dictionary<string, object> inputNamesValues = new Dictionary<string, object>();
			inputNamesValues["resource"] = @resource;
			inputNamesValues["reservation"] = @reservation;
			inputNamesValues["connectors"] = @connectors;
			inputNamesValues["connectorsAttributes"] = @connectorsAttributes;
			Dictionary<string, Type> outputNamesTypes = new Dictionary<string, Type>();
			outputNamesTypes["out"] = typeof(string);
			Dictionary<string, object> outputNamesValues = m_PopulateResourcesFunctionInterpreter.Run(callId, inputNamesValues, outputNamesTypes);
			@out =  (string)outputNamesValues["out"];
		}

		[Description("This function is called (automatically by the server) only once when the driver is going to be unloaded.\r\nUse this function to close any open sessions, saving states and any information that might be needed for the next executions of the driver commands (these can be loaded again in the Init function).")]
		[Folder("Initialization")]
		[EndSession,Hidden]
		[Cancelable]
		public void @EndSession()
		{
			lock(m_EndSessionFunctionInterpreterLock)
			{
				if(m_EndSessionFunctionInterpreter == null)
					m_EndSessionFunctionInterpreter = CreateFunctionInterpreter("onrack\\Initialization\\EndSession.tsdrv");
			}
			Guid callId = Guid.Empty;
			if(CancellationContext.Current != null)
				callId = CancellationContext.Current.CallId;
			Dictionary<string, object> inputNamesValues = new Dictionary<string, object>();
			Dictionary<string, Type> outputNamesTypes = new Dictionary<string, Type>();
			Dictionary<string, object> outputNamesValues = m_EndSessionFunctionInterpreter.Run(callId, inputNamesValues, outputNamesTypes);
		}

		[Description("This function is called (automatically by the server) only once when the driver is being loaded for the first time.\r\nThis function will not get information on a specific reservation so make sure to only do initialization tasks in this function that are cross reservations.\r\nWhen several resources are using the same driver, the Init function will be called for each one of them when the driver will be used for the first time or after an idle time.")]
		[Folder("Initialization")]
		[StartSession,Hidden]
		[Cancelable]
		public void @Init([Description("A predefined matrix with the following columns: attribute, mandatory / optional (empty is mandatory), value - this column will be automatically populated when executing the command.")][Alias("resource")][ParameterDefaultValue("{['ResourceName','','';'ResourceFullName','','';'ResourceFamily','','';'ResourceModel','','';'ResourceDescription','','';'OnRack Address','','';'OnRack Username','','';'OnRack Password','','']}")]  string[,] @resource, [Description("A predefined matrix with the following columns: parameter, mandatory / optional (empty is mandatory), value - this column will be automatically populated when executing the command.")][Alias("connectivityInfo")][ParameterDefaultValue("{['ServerAddress','','';'TestShellApiPort','','';'QualiApiPort','','';'AdminUsername','','';'AdminPassword','','']}")]  string[,] @connectivityInfo)
		{
			lock(m_InitFunctionInterpreterLock)
			{
				if(m_InitFunctionInterpreter == null)
					m_InitFunctionInterpreter = CreateFunctionInterpreter("onrack\\Initialization\\Init.tsdrv");
			}
			Guid callId = Guid.Empty;
			if(CancellationContext.Current != null)
				callId = CancellationContext.Current.CallId;
			Dictionary<string, object> inputNamesValues = new Dictionary<string, object>();
			inputNamesValues["resource"] = @resource;
			inputNamesValues["connectivityInfo"] = @connectivityInfo;
			Dictionary<string, Type> outputNamesTypes = new Dictionary<string, Type>();
			Dictionary<string, object> outputNamesValues = m_InitFunctionInterpreter.Run(callId, inputNamesValues, outputNamesTypes);
		}

		[Description("This function is being called when the user/admin selects to reset the driver.\r\nThis function can be used to close open sessions or clear any saved values, and then call the Init function to start over again.")]
		[Folder("Initialization")]
		[Cancelable]
		public void @ResetDriver([Description("A predefined matrix with the following columns: attribute, mandatory / optional (empty is mandatory), value - this column will be automatically populated when executing the command.")][Alias("resource")][ParameterDefaultValue("{['ResourceName','','';'ResourceFullName','','';'ResourceFamily','','';'ResourceModel','','';'ResourceDescription','','']}")]  string[,] @resource, [Description("A predefined matrix with the following columns: parameter, mandatory / optional (empty is mandatory), value - this column will be automatically populated when executing the command.")][Alias("connectivityInfo")][ParameterDefaultValue("{['ServerAddress','','';'ServerPort','','']}")]  string[,] @connectivityInfo)
		{
			lock(m_ResetDriverFunctionInterpreterLock)
			{
				if(m_ResetDriverFunctionInterpreter == null)
					m_ResetDriverFunctionInterpreter = CreateFunctionInterpreter("onrack\\Initialization\\ResetDriver.tsdrv");
			}
			Guid callId = Guid.Empty;
			if(CancellationContext.Current != null)
				callId = CancellationContext.Current.CallId;
			Dictionary<string, object> inputNamesValues = new Dictionary<string, object>();
			inputNamesValues["resource"] = @resource;
			inputNamesValues["connectivityInfo"] = @connectivityInfo;
			Dictionary<string, Type> outputNamesTypes = new Dictionary<string, Type>();
			Dictionary<string, object> outputNamesValues = m_ResetDriverFunctionInterpreter.Run(callId, inputNamesValues, outputNamesTypes);
		}

		[Folder("OnRack Functions")]
		[Cancelable]
		public void @DeployESX([Description("Deploy on a host with the provided MAC address. Use either this option or the OnRackID option. ")][Alias("MAC")]  string @MAC, [Alias("ESX_Hostname")]  string @ESX_Hostname, [Alias("ESX_IP")]  string @ESX_IP, [Alias("ESX_Gateway")]  string @ESX_Gateway, [Alias("ESX_RootPass")]  string @ESX_RootPass, [Alias("ESX_Domain")]  string @ESX_Domain, [Alias("ESX_DNS1")]  string @ESX_DNS1, [Alias("ESX_DNS2")]  string @ESX_DNS2, [Alias("TaskID")] out string @TaskID)
		{
			lock(m_DeployESXFunctionInterpreterLock)
			{
				if(m_DeployESXFunctionInterpreter == null)
					m_DeployESXFunctionInterpreter = CreateFunctionInterpreter("onrack\\OnRack Functions\\DeployESX.tsdrv");
			}
			Guid callId = Guid.Empty;
			if(CancellationContext.Current != null)
				callId = CancellationContext.Current.CallId;
			Dictionary<string, object> inputNamesValues = new Dictionary<string, object>();
			inputNamesValues["MAC"] = @MAC;
			inputNamesValues["ESX_Hostname"] = @ESX_Hostname;
			inputNamesValues["ESX_IP"] = @ESX_IP;
			inputNamesValues["ESX_Gateway"] = @ESX_Gateway;
			inputNamesValues["ESX_RootPass"] = @ESX_RootPass;
			inputNamesValues["ESX_Domain"] = @ESX_Domain;
			inputNamesValues["ESX_DNS1"] = @ESX_DNS1;
			inputNamesValues["ESX_DNS2"] = @ESX_DNS2;
			Dictionary<string, Type> outputNamesTypes = new Dictionary<string, Type>();
			outputNamesTypes["TaskID"] = typeof(string);
			Dictionary<string, object> outputNamesValues = m_DeployESXFunctionInterpreter.Run(callId, inputNamesValues, outputNamesTypes);
			@TaskID =  (string)outputNamesValues["TaskID"];
		}

		[Folder("OnRack Functions")]
		[Cancelable]
		public void @GetTasks([Alias("TaskIDs")] out string[] @TaskIDs)
		{
			lock(m_GetTasksFunctionInterpreterLock)
			{
				if(m_GetTasksFunctionInterpreter == null)
					m_GetTasksFunctionInterpreter = CreateFunctionInterpreter("onrack\\OnRack Functions\\GetTasks.tsdrv");
			}
			Guid callId = Guid.Empty;
			if(CancellationContext.Current != null)
				callId = CancellationContext.Current.CallId;
			Dictionary<string, object> inputNamesValues = new Dictionary<string, object>();
			Dictionary<string, Type> outputNamesTypes = new Dictionary<string, Type>();
			outputNamesTypes["Tasks"] = typeof(string[]);
			Dictionary<string, object> outputNamesValues = m_GetTasksFunctionInterpreter.Run(callId, inputNamesValues, outputNamesTypes);
			@TaskIDs =  (string[])outputNamesValues["Tasks"];
		}

		[Folder("OnRack Functions")]
		[Cancelable]
		public void @GetTaskStatus([Alias("TaskID")]  string @TaskID, [Alias("Status")] out string[,] @Status)
		{
			lock(m_GetTaskStatusFunctionInterpreterLock)
			{
				if(m_GetTaskStatusFunctionInterpreter == null)
					m_GetTaskStatusFunctionInterpreter = CreateFunctionInterpreter("onrack\\OnRack Functions\\GetTaskStatus.tsdrv");
			}
			Guid callId = Guid.Empty;
			if(CancellationContext.Current != null)
				callId = CancellationContext.Current.CallId;
			Dictionary<string, object> inputNamesValues = new Dictionary<string, object>();
			inputNamesValues["TaskID"] = @TaskID;
			Dictionary<string, Type> outputNamesTypes = new Dictionary<string, Type>();
			outputNamesTypes["Status"] = typeof(string[,]);
			Dictionary<string, object> outputNamesValues = m_GetTaskStatusFunctionInterpreter.Run(callId, inputNamesValues, outputNamesTypes);
			@Status =  (string[,])outputNamesValues["Status"];
		}

		[Folder("OnRack Functions")]
		[Cancelable]
		public void @PopulateSystem([Alias("AllResources")] out string[,] @AllResources)
		{
			lock(m_PopulateSystemFunctionInterpreterLock)
			{
				if(m_PopulateSystemFunctionInterpreter == null)
					m_PopulateSystemFunctionInterpreter = CreateFunctionInterpreter("onrack\\OnRack Functions\\PopulateSystem.tsdrv");
			}
			Guid callId = Guid.Empty;
			if(CancellationContext.Current != null)
				callId = CancellationContext.Current.CallId;
			Dictionary<string, object> inputNamesValues = new Dictionary<string, object>();
			Dictionary<string, Type> outputNamesTypes = new Dictionary<string, Type>();
			outputNamesTypes["AllResources"] = typeof(string[,]);
			Dictionary<string, object> outputNamesValues = m_PopulateSystemFunctionInterpreter.Run(callId, inputNamesValues, outputNamesTypes);
			@AllResources =  (string[,])outputNamesValues["AllResources"];
		}

		[Folder("OnRack Functions")]
		[Cancelable]
		public void @WaitForTask([Alias("TaskID")]  string @TaskID, [Alias("MaxWaitSeconds")]  double @MaxWaitSeconds)
		{
			lock(m_WaitForTaskFunctionInterpreterLock)
			{
				if(m_WaitForTaskFunctionInterpreter == null)
					m_WaitForTaskFunctionInterpreter = CreateFunctionInterpreter("onrack\\OnRack Functions\\WaitForTask.tsdrv");
			}
			Guid callId = Guid.Empty;
			if(CancellationContext.Current != null)
				callId = CancellationContext.Current.CallId;
			Dictionary<string, object> inputNamesValues = new Dictionary<string, object>();
			inputNamesValues["TaskID"] = @TaskID;
			inputNamesValues["MaxWaitSeconds"] = @MaxWaitSeconds;
			Dictionary<string, Type> outputNamesTypes = new Dictionary<string, Type>();
			Dictionary<string, object> outputNamesValues = m_WaitForTaskFunctionInterpreter.Run(callId, inputNamesValues, outputNamesTypes);
		}


   
        #region DucktypingProxy
        
		[DebuggerStepThrough]
		internal class DucktypingProxy<TTarget> : RealProxy where TTarget : class
		{
			private object m_Target;

			public DucktypingProxy(object target) : base(typeof(TTarget))
			{
				m_Target = target;
			}

			[SecurityPermission(SecurityAction.LinkDemand, Flags = SecurityPermissionFlag.Infrastructure)]
			public override IMessage Invoke(IMessage msg)
			{
				IMethodCallMessage methodMessage = new MethodCallMessageWrapper((IMethodCallMessage)msg);
				MethodBase method = methodMessage.MethodBase;
				object returnValue = null;
				ReturnMessage returnMessage = null;

				try
				{
					MethodBase targetMethod = GetTargetMethodFromInterfaceMethod(method);
					if (targetMethod == null)
						throw new NotImplementedException(string.Format("Method {0} was not implemented by the target", method.Name));
					returnValue = targetMethod.Invoke(m_Target, methodMessage.Args);
					returnMessage = new ReturnMessage(returnValue, methodMessage.Args, methodMessage.ArgCount, methodMessage.LogicalCallContext, methodMessage);
				}
				catch (Exception ex)
				{
					if ((ex is RemotingException || ex is TargetInvocationException)
						&& ex.InnerException != null)
						ex = ex.InnerException;

					returnMessage = new ReturnMessage(ex, methodMessage);
				}

				return returnMessage;
			}

			private MethodBase GetTargetMethodFromInterfaceMethod(MethodBase interfaceMethod)
			{
				ParameterInfo[] interfaceMethodParameters = interfaceMethod.GetParameters();
				Type[] parameterTypes = new Type[interfaceMethodParameters.Length];
				for (int i = 0; i < parameterTypes.Length; i++)
				{
					parameterTypes[i] = interfaceMethodParameters[i].ParameterType;
				}

				MethodInfo targetMethod;
				if (interfaceMethod.IsGenericMethod)
					targetMethod = m_Target.GetType().GetMethod(interfaceMethod.Name, parameterTypes).MakeGenericMethod(interfaceMethod.GetGenericArguments());
				else
					targetMethod = m_Target.GetType().GetMethod(interfaceMethod.Name, parameterTypes);

				return targetMethod;
			}

			public TTarget TransparentProxy
			{
				get
				{
					return base.GetTransparentProxy() as TTarget;
				}
			}
		}
		
		#endregion DucktypingProxy
		
		#region TestShellRuntimeLocator

        internal class TestShellRuntimeLocator
        {
            private const string RuntimeRepositoryPath = @"Software\QualiSystems\TestShellRuntime";

            public Assembly RuntimeAssembly { get; private set; }
            public string RuntimeTypeName { get; private set; }

            public TestShellRuntimeLocator(string targetRuntimeVersion)
            {
				Trace.WriteLine("Quali Runtime: Target runtime version is " +targetRuntimeVersion+ ", searching for matching installed versions...");
                var runtimeInfos = ReadInstalledTestShellRuntimeInfos(targetRuntimeVersion);
                TestShellRuntimeInfo selectedRuntimeInfo = SelectRuntimeVersionInfo(runtimeInfos, targetRuntimeVersion);
                RuntimeTypeName = selectedRuntimeInfo.RuntimeTypeName;
                string runtimeAssemblyPath = Path.Combine(selectedRuntimeInfo.Path, selectedRuntimeInfo.RuntimeAssemblyName);
                if (!System.IO.File.Exists(runtimeAssemblyPath))
                    throw RuntimeAssemblyNotFound(runtimeAssemblyPath);
                Trace.WriteLine("Quali Runtime: Loading runtime version " +selectedRuntimeInfo.Version+ " from " + runtimeAssemblyPath);
                RuntimeAssembly = Assembly.LoadFrom(runtimeAssemblyPath);
            }

            private static TestShellRuntimeInfo SelectRuntimeVersionInfo(IEnumerable<TestShellRuntimeInfo> runtimeInfos, string targetRuntimeVersion)
            {
                TestShellRuntimeInfo runtimeInfo = GetCurrentlyLoadedRuntimeInfo(runtimeInfos);
                if (runtimeInfo != null)
                {
                    if(!IsGreaterOrEqualVersion(runtimeInfo.Version, targetRuntimeVersion))
                        throw IncompatibleRuntimeLoaded(targetRuntimeVersion, runtimeInfo.Version);
                }
                else
                {
					var matchingRuntimeInfos = GetMatchingRuntimeInfos(runtimeInfos, targetRuntimeVersion);
					if (!matchingRuntimeInfos.Any())
						throw NoMatchingRuntimeException(targetRuntimeVersion);

					var licensedRuntimeInfos = GetLicensedRuntimeInfos(matchingRuntimeInfos);
					if (!licensedRuntimeInfos.Any())
						throw NoRuntimeLicenseException(targetRuntimeVersion);

                    runtimeInfo = GetBestMatchRuntimeInfo(licensedRuntimeInfos);
                }
                return runtimeInfo;
            }

			private static IEnumerable<TestShellRuntimeInfo> GetMatchingRuntimeInfos(IEnumerable<TestShellRuntimeInfo> runtimeInfos, string targetRuntimeVersion)
            {
				return runtimeInfos.
                    Where(r => IsGreaterOrEqualVersion(r.Version, targetRuntimeVersion)).	//only matching versions
					ToList();
			}
			
			private static IEnumerable<TestShellRuntimeInfo> GetLicensedRuntimeInfos(IEnumerable<TestShellRuntimeInfo> runtimeInfos)
			{
				return runtimeInfos.
					Where(IsLicenseValid).													//only licensed runtimes
					ToList();
			}

            private static TestShellRuntimeInfo GetBestMatchRuntimeInfo(IEnumerable<TestShellRuntimeInfo> runtimeInfos)
            {
                TestShellRuntimeInfo bestMatchRuntimeInfo = runtimeInfos.                    
                    OrderBy(r=>VersionStringToComparableNumber(r.Version)).FirstOrDefault();//best match
                return bestMatchRuntimeInfo;
            }

			private static bool IsLicenseValid(TestShellRuntimeInfo testShellRuntimeInfo)
			{
				string runtimeAssemblyPath = Path.Combine(testShellRuntimeInfo.Path, testShellRuntimeInfo.RuntimeAssemblyName);
				AppDomainSetup appDomainSetup = new AppDomainSetup();
				appDomainSetup.ApplicationBase = testShellRuntimeInfo.Path;
				AppDomain appDomain = AppDomain.CreateDomain("LicenseValidationDomain", AppDomain.CurrentDomain.Evidence, appDomainSetup);
				UnloadableLicenseValidator unloadableLicenseValidator = (UnloadableLicenseValidator)appDomain.CreateInstanceFromAndUnwrap(
                Assembly.GetExecutingAssembly().CodeBase, "QualiSystems.Driver.onrack+TestShellRuntimeLocator+UnloadableLicenseValidator");
				bool isRuntimeLicenseValid = unloadableLicenseValidator.IsLicenseValid(runtimeAssemblyPath, testShellRuntimeInfo.RuntimeLicenseValidatorTypeName);
				AppDomain.Unload(appDomain);
				Trace.WriteLine("Quali Runtime: Runtime at " +testShellRuntimeInfo.Path+ " is " + (isRuntimeLicenseValid ? "Licensed" : "Unlicenced"));
				return isRuntimeLicenseValid;
			}

            private static bool IsGreaterOrEqualVersion(string comparedVersion, string baseVersion)
            {
                int comparedVersionWeighted = VersionStringToComparableNumber(comparedVersion);
                int baseVersionWeighted = VersionStringToComparableNumber(baseVersion);
                return comparedVersionWeighted >= baseVersionWeighted;
            }

            private static int VersionStringToComparableNumber(string version)
            {
                string[] versionParts = version.Split('.');
                int major = int.Parse(versionParts[0]);
                int minor = int.Parse(versionParts[1]);
                return (major << 16) + minor;
            }

            private static TestShellRuntimeInfo GetCurrentlyLoadedRuntimeInfo(IEnumerable<TestShellRuntimeInfo> readTestShellRuntimeInfo)
            {
                TestShellRuntimeInfo matchingRuntime = null;
                foreach (var loadedAssembly in AppDomain.CurrentDomain.GetAssemblies())
                {
                    try
                    {
                        matchingRuntime = readTestShellRuntimeInfo.FirstOrDefault(r => string.Equals(loadedAssembly.Location, Path.Combine(r.Path, r.RuntimeAssemblyName), StringComparison.InvariantCultureIgnoreCase));
                        if (matchingRuntime != null)
						{
							Trace.WriteLine("Quali Runtime: "+ string.Format("Runtime version {0} already loaded.", matchingRuntime.Version));
                            break;
						}
                    }
                    catch (NotSupportedException)
                    {}
                }
                return matchingRuntime;
            }

            private static IEnumerable<TestShellRuntimeInfo> ReadInstalledTestShellRuntimeInfos(string targetRuntimeVersion)
            {
                RegistryKey testShellRuntimeRepositoryKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry32).OpenSubKey(RuntimeRepositoryPath);
                if (testShellRuntimeRepositoryKey == null || testShellRuntimeRepositoryKey.SubKeyCount == 0)
                    throw NoMatchingRuntimeException(targetRuntimeVersion);

                List<TestShellRuntimeInfo> testShellRuntimeInfos = new List<TestShellRuntimeInfo>();
                foreach (var subKeyName in testShellRuntimeRepositoryKey.GetSubKeyNames())
                {
                    var runtimeKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry32).OpenSubKey(Path.Combine(RuntimeRepositoryPath,subKeyName));
                    TestShellRuntimeInfo testShellRuntimeInfo = new TestShellRuntimeInfo();
                    testShellRuntimeInfo.Path = (string) runtimeKey.GetValue("Path");
                    testShellRuntimeInfo.Version = (string)runtimeKey.GetValue("RuntimeVersion") ?? (string)runtimeKey.GetValue("Version");
                    testShellRuntimeInfo.RuntimeAssemblyName = (string)runtimeKey.GetValue("RuntimeAssembly");
                    testShellRuntimeInfo.RuntimeTypeName = (string)runtimeKey.GetValue("RuntimeType");
                    testShellRuntimeInfo.RuntimeLicenseValidatorTypeName = (string)runtimeKey.GetValue("RuntimeLicenseValidatorType");
                    testShellRuntimeInfos.Add(testShellRuntimeInfo);
                }
                return testShellRuntimeInfos;
            }

            private static Exception IncompatibleRuntimeLoaded(string targetRuntimeVersion, string loadedRuntimeVersion)
            {
                return new ApplicationException(string.Format("Quali runtime version {0} needed but version {1} already loaded.", targetRuntimeVersion, loadedRuntimeVersion));
            }

            private static Exception RuntimeAssemblyNotFound(string runtimeAssemblyPath)
            {
                return new ApplicationException("Runtime assembly "+runtimeAssemblyPath+" is missing.");
            }

			public static Exception NoMatchingRuntimeException(string targetRuntimeVersion)
			{
				return TestShellRuntimeException("Could not find a matching TestShell Runtime with version " + targetRuntimeVersion,
												 targetRuntimeVersion,
												 "MatchingRuntimeNotFound");
			}

			private static Exception NoRuntimeLicenseException(string targetRuntimeVersion)
			{
				return TestShellRuntimeException("Could not find a license for TestShell Runtime version " + targetRuntimeVersion,
												 targetRuntimeVersion,
												 "RuntimeLicenseNotFound");
			}

			private static Exception TestShellRuntimeException(string description, string targetRuntimeVersion, string reason)
			{
				KeyValuePair<string, string>[] parameters = new[]
				{
					new KeyValuePair<string, string>("Target Version", targetRuntimeVersion),
					new KeyValuePair<string, string>("Reason", reason)
				};
				return new ErrorException("Quali Runtime", description, string.Empty, parameters);
			}

            private class TestShellRuntimeInfo
            {
                public string Path { get; set; }
                public string Version { get; set; }
                public string RuntimeAssemblyName { get; set; }
                public string RuntimeTypeName { get; set; }
                public string RuntimeLicenseValidatorTypeName { get; set; }
            }

			internal class UnloadableLicenseValidator : MarshalByRefObject
			{
				public bool IsLicenseValid(string runtimeAssemblyPath, string runtimeLicenseValidatorTypeName)
				{
					Assembly runtimeAssembly = Assembly.LoadFrom(runtimeAssemblyPath);
					Type runtimeLicenseValidatorType = runtimeAssembly.GetType(runtimeLicenseValidatorTypeName);
					bool isRuntimeLicenseValid = (bool)runtimeLicenseValidatorType.GetMethod("IsRuntimeLicenseValid").Invoke(null, null);
					return isRuntimeLicenseValid;
				}
			}
        }

        #endregion TestShellRuntimeLocator

		interface IFunctionInterpreter
		{
			Dictionary<string, object> Run(Guid callId, Dictionary<string, object> inputNamesValues, Dictionary<string, Type> outputNamesTypes);
		}
    }

		public enum YesNo
	{
		No=0,
		Yes=1
	}


}