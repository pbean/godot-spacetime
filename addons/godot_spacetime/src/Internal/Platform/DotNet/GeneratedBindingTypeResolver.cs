using System;
using System.Linq;
using System.Reflection;
using SpacetimeDB;

namespace GodotSpacetime.Runtime.Platform.DotNet;

internal static class GeneratedBindingTypeResolver
{
    internal static Type ResolveDbConnectionType(string? generatedBindingsNamespace)
    {
        var resolvedNamespace = NormalizeGeneratedBindingsNamespace(generatedBindingsNamespace);
        var fullName = $"{resolvedNamespace}.DbConnection";
        var dbConnectionType = ResolveType(
            fullName,
            candidate => candidate != null
                && typeof(IDbConnection).IsAssignableFrom(candidate)
                && candidate.GetMethod(
                    "Builder",
                    BindingFlags.Public | BindingFlags.Static | BindingFlags.FlattenHierarchy) != null,
            "DbConnection");

        return dbConnectionType;
    }

    internal static Type ResolveRemoteTablesType(string? generatedBindingsNamespace)
    {
        var resolvedNamespace = NormalizeGeneratedBindingsNamespace(generatedBindingsNamespace);
        var fullName = $"{resolvedNamespace}.RemoteTables";
        return ResolveType(
            fullName,
            candidate => candidate != null && candidate.IsClass,
            "RemoteTables");
    }

    internal static Type? TryResolveRemoteTablesType(string? generatedBindingsNamespace)
    {
        try
        {
            return ResolveRemoteTablesType(generatedBindingsNamespace);
        }
        catch (InvalidOperationException)
        {
            return null;
        }
    }

    internal static string[] GetRemoteTableNames(string? generatedBindingsNamespace)
    {
        var remoteTablesType = TryResolveRemoteTablesType(generatedBindingsNamespace);
        if (remoteTablesType == null)
            return Array.Empty<string>();

        return remoteTablesType
            .GetProperties(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Select(property => property.Name)
            .Concat(
                remoteTablesType
                    .GetFields(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly)
                    .Select(field => field.Name))
            .Distinct(StringComparer.Ordinal)
            .OrderBy(name => name, StringComparer.Ordinal)
            .ToArray();
    }

    private static string NormalizeGeneratedBindingsNamespace(string? generatedBindingsNamespace) =>
        string.IsNullOrWhiteSpace(generatedBindingsNamespace)
            ? SpacetimeSettings.DefaultGeneratedBindingsNamespace
            : generatedBindingsNamespace.Trim();

    private static Type ResolveType(string fullName, Func<Type?, bool> validator, string shortTypeName)
    {
        foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
        {
            var candidate = assembly.GetType(fullName, throwOnError: false);
            if (validator(candidate))
                return candidate!;
        }

        throw new InvalidOperationException(
            $"Generated bindings are required before resolving {shortTypeName}. " +
            $"Expected type '{fullName}' to be available in a loaded assembly.");
    }
}
