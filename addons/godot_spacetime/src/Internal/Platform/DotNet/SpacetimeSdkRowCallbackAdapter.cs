using System;
using System.Collections.Generic;
using System.Linq.Expressions;
using System.Reflection;
using System.Runtime.CompilerServices;
using SpacetimeDB;

namespace GodotSpacetime.Runtime.Platform.DotNet;

internal interface IRowChangeEventSink
{
    void OnRowInserted(string tableName, object row);
    void OnRowDeleted(string tableName, object row);
    void OnRowUpdated(string tableName, object oldRow, object newRow);
}

/// <summary>
/// Adapter for the SpacetimeDB .NET ClientSDK row-level change callback layer.
///
/// This class is the ONLY location in the codebase where SpacetimeDB.ClientSDK
/// row callback events may be referenced directly. Hooks into the generated
/// RemoteTableHandle events (OnInsert, OnDelete, OnUpdate) via reflection and
/// Expression trees, routing them to the GodotSpacetime-neutral
/// <see cref="IRowChangeEventSink"/> interface.
///
/// See <c>docs/runtime-boundaries.md</c> — "Internal/Platform/DotNet/ — The Runtime
/// Isolation Zone" for the architectural justification.
/// </summary>
internal sealed class SpacetimeSdkRowCallbackAdapter
{
    private readonly ConditionalWeakTable<object, RegistrationMarker> _registeredDbs = new();

    private sealed class RegistrationMarker;

    internal void ClearRegistration()
    {
        _registeredDbs.Clear();
    }

    /// <summary>
    /// Registers insert, update, and delete callbacks on all table handles found in the
    /// generated RemoteTables object. Each callback routes row change events to
    /// <paramref name="sink"/> with the table name and boxed row values.
    ///
    /// Call immediately after <c>OnConnected</c> fires, with the live RemoteTables object
    /// from <c>SpacetimeSdkConnectionAdapter.GetDb()</c>. On disconnect, call
    /// <see cref="ClearRegistration"/> so the next connection gets fresh callbacks
    /// instead of relying on GC to clear the weak-table entries.
    /// </summary>
    internal void RegisterCallbacks(object db, IRowChangeEventSink sink)
    {
        ArgumentNullException.ThrowIfNull(db);
        ArgumentNullException.ThrowIfNull(sink);

        // The generated RemoteTables shape is field-backed today, but keep property support so
        // future generator changes do not break callback wiring. Guard repeated registration
        // because the same live Db object can transition through Degraded -> Connected on recovery.
        if (!_registeredDbs.TryGetValue(db, out _))
            _registeredDbs.Add(db, new RegistrationMarker());
        else
            return;

        var seenHandles = new HashSet<object>(ReferenceEqualityComparer.Instance);

        foreach (var field in db.GetType().GetFields(BindingFlags.Public | BindingFlags.Instance))
        {
            TryRegisterTableHandle(field.Name, field.GetValue(db), sink, seenHandles);
        }

        foreach (var prop in db.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            if (prop.GetIndexParameters().Length != 0)
                continue;

            TryRegisterTableHandle(prop.Name, prop.GetValue(db), sink, seenHandles);
        }
    }

    private static void TryRegisterTableHandle(
        string tableName,
        object? tableHandle,
        IRowChangeEventSink sink,
        ISet<object> seenHandles)
    {
        if (tableHandle == null || !seenHandles.Add(tableHandle))
            return;

        TryWireRowEvent(tableHandle, "OnInsert", tableName, sink, isDelete: false);
        TryWireRowEvent(tableHandle, "OnDelete", tableName, sink, isDelete: true);
        TryWireUpdateEvent(tableHandle, tableName, sink);
    }

    private static void TryWireRowEvent(
        object tableHandle,
        string eventName,
        string tableName,
        IRowChangeEventSink sink,
        bool isDelete)
    {
        var evt = tableHandle.GetType().GetEvent(eventName);
        if (evt?.EventHandlerType == null) return;

        var invoke = evt.EventHandlerType.GetMethod("Invoke");
        if (invoke == null) return;

        var parameters = invoke.GetParameters();
        if (parameters.Length != 2) return;   // (TContext context, TRow row)

        var ctxParam = Expression.Parameter(parameters[0].ParameterType, "ctx");
        var rowParam = Expression.Parameter(parameters[1].ParameterType, "row");
        var sinkConst = Expression.Constant(sink);
        var tableNameConst = Expression.Constant(tableName);
        var rowAsObject = Expression.Convert(rowParam, typeof(object));

        var sinkMethod = isDelete
            ? typeof(IRowChangeEventSink).GetMethod(nameof(IRowChangeEventSink.OnRowDeleted))!
            : typeof(IRowChangeEventSink).GetMethod(nameof(IRowChangeEventSink.OnRowInserted))!;

        var body = Expression.Call(sinkConst, sinkMethod, tableNameConst, rowAsObject);
        var lambda = Expression.Lambda(evt.EventHandlerType, body, ctxParam, rowParam).Compile();
        evt.AddEventHandler(tableHandle, (Delegate)lambda);
    }

    private static void TryWireUpdateEvent(object tableHandle, string tableName, IRowChangeEventSink sink)
    {
        var evt = tableHandle.GetType().GetEvent("OnUpdate");
        if (evt?.EventHandlerType == null) return;

        var invoke = evt.EventHandlerType.GetMethod("Invoke");
        if (invoke == null) return;

        var parameters = invoke.GetParameters();
        if (parameters.Length != 3) return;   // (TContext context, TRow oldRow, TRow newRow)

        var ctxParam = Expression.Parameter(parameters[0].ParameterType, "ctx");
        var oldRowParam = Expression.Parameter(parameters[1].ParameterType, "oldRow");
        var newRowParam = Expression.Parameter(parameters[2].ParameterType, "newRow");
        var sinkConst = Expression.Constant(sink);
        var tableNameConst = Expression.Constant(tableName);
        var oldRowAsObject = Expression.Convert(oldRowParam, typeof(object));
        var newRowAsObject = Expression.Convert(newRowParam, typeof(object));

        var sinkMethod = typeof(IRowChangeEventSink).GetMethod(nameof(IRowChangeEventSink.OnRowUpdated))!;
        var body = Expression.Call(sinkConst, sinkMethod, tableNameConst, oldRowAsObject, newRowAsObject);
        var lambda = Expression.Lambda(evt.EventHandlerType, body, ctxParam, oldRowParam, newRowParam).Compile();
        evt.AddEventHandler(tableHandle, (Delegate)lambda);
    }
}
