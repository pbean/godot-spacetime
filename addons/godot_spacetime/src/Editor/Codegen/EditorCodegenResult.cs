#if TOOLS
namespace GodotSpacetime.Editor.Codegen;

public readonly record struct EditorCodegenResult(
    bool IsSuccess,
    string StatusMessage,
    string? ErrorDetail)
{
    public static EditorCodegenResult Success(string statusMessage) =>
        new(true, statusMessage, null);

    public static EditorCodegenResult Failure(string statusMessage, string? errorDetail) =>
        new(false, statusMessage, errorDetail);
}
#endif
