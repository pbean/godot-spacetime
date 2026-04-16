using System;
using System.IO;
using System.Linq;
using System.Reflection;
using SpacetimeDB.ClientApi;

namespace GodotSpacetime.Runtime.Platform.DotNet;

internal sealed class SpacetimeSdkTelemetrySerializer
{
    private static readonly ClientMessage.BSATN ClientMessageSerializer = new();

    internal long MeasureSubscribePayloadBytes(string[] querySqls)
    {
        ArgumentNullException.ThrowIfNull(querySqls);

        var message = new ClientMessage.Subscribe(new Subscribe
        {
            RequestId = 1,
            QuerySetId = new QuerySetId { Id = 1 },
            QueryStrings = querySqls.ToList(),
        });

        return MeasureClientMessageBytes(message);
    }

    internal long MeasureUnsubscribePayloadBytes()
    {
        var message = new ClientMessage.Unsubscribe(new Unsubscribe
        {
            RequestId = 1,
            QuerySetId = new QuerySetId { Id = 1 },
            Flags = default,
        });

        return MeasureClientMessageBytes(message);
    }

    internal long MeasureOneOffQueryPayloadBytes(string sqlClause)
    {
        if (string.IsNullOrWhiteSpace(sqlClause))
            throw new ArgumentException("One-off query telemetry requires a non-empty SQL clause.", nameof(sqlClause));

        var message = new ClientMessage.OneOffQuery(new OneOffQuery
        {
            RequestId = 1,
            QueryString = sqlClause,
        });

        return MeasureClientMessageBytes(message);
    }

    internal long MeasureReducerPayloadBytes(object reducerArgs, string reducerName)
    {
        ArgumentNullException.ThrowIfNull(reducerArgs);
        ArgumentException.ThrowIfNullOrWhiteSpace(reducerName);

        var reducerPayload = SerializeReducerArgs(reducerArgs);
        var message = new ClientMessage.CallReducer(new CallReducer
        {
            RequestId = 1,
            Flags = 0,
            Reducer = reducerName,
            Args = reducerPayload.ToList(),
        });

        return MeasureClientMessageBytes(message);
    }

    private static long MeasureClientMessageBytes(ClientMessage message)
    {
        using var stream = new MemoryStream();
        using var writer = new BinaryWriter(stream);
        ClientMessageSerializer.Write(writer, message);
        writer.Flush();
        return stream.Length;
    }

    private static byte[] SerializeReducerArgs(object reducerArgs)
    {
        var writeFieldsMethod = reducerArgs.GetType().GetMethod(
            "WriteFields",
            BindingFlags.Public | BindingFlags.Instance,
            null,
            [typeof(BinaryWriter)],
            null);

        if (writeFieldsMethod == null)
        {
            throw new InvalidOperationException(
                $"Reducer args type '{reducerArgs.GetType().FullName ?? reducerArgs.GetType().Name}' " +
                "does not expose WriteFields(BinaryWriter); cannot measure outbound bytes honestly.");
        }

        using var stream = new MemoryStream();
        using var writer = new BinaryWriter(stream);
        writeFieldsMethod.Invoke(reducerArgs, [writer]);
        writer.Flush();
        return stream.ToArray();
    }
}
