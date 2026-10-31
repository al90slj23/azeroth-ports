// Project-local, deliberately bounded Ghidra inspection; not a stock REA provider.
import java.nio.file.Files;
import java.nio.file.Path;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.util.headless.HeadlessScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.SourceType;

public class AzerothFocusedDecompile extends HeadlessScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2) throw new IllegalArgumentException("output.json and selection.json required");
        JsonArray selected = com.google.gson.JsonParser.parseString(Files.readString(Path.of(args[1]))).getAsJsonArray();
        JsonObject report = new JsonObject();
        report.addProperty("method", "project-local-ghidra-noanalysis-selected-pdata-functions");
        report.addProperty("automatic_analysis", false);
        report.addProperty("target_executed", false);
        report.addProperty("ghidra_version", ghidra.framework.Application.getApplicationVersion());
        report.addProperty("language", currentProgram.getLanguageID().toString());
        report.addProperty("compiler_spec", currentProgram.getCompilerSpec().getCompilerSpecID().toString());
        report.addProperty("image_base", currentProgram.getImageBase().toString());
        JsonArray functions = new JsonArray();
        report.add("functions", functions);
        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) throw new IllegalStateException(decompiler.getLastMessage());
        try {
            for (var item : selected) {
                monitor.checkCancelled();
                JsonObject selection = item.getAsJsonObject();
                Address start = toAddr(selection.get("start").getAsString());
                Address endExclusive = toAddr(selection.get("end_exclusive").getAsString());
                AddressSet range = new AddressSet(start, endExclusive.subtract(1));
                JsonObject result = new JsonObject();
                result.add("selection", selection.deepCopy());
                functions.add(result);
                try {
                    DisassembleCommand command = new DisassembleCommand(start, range, true);
                    command.enableCodeAnalysis(false);
                    result.addProperty("disassembled", command.applyTo(currentProgram, monitor));
                    result.addProperty("disassembly_status", command.getStatusMsg());
                    Function existing = currentProgram.getFunctionManager().getFunctionAt(start);
                    if (existing != null) currentProgram.getFunctionManager().removeFunction(start);
                    Function function = currentProgram.getFunctionManager().createFunction(
                        "selected_" + start.toString(), start, range, SourceType.USER_DEFINED);
                    JsonArray assembly = new JsonArray();
                    JsonArray crossingEnd = new JsonArray();
                    JsonArray computedJumps = new JsonArray();
                    int decodedBytes = 0;
                    InstructionIterator instructions = currentProgram.getListing().getInstructions(range, true);
                    while (instructions.hasNext()) {
                        Instruction instruction = instructions.next();
                        JsonObject line = new JsonObject();
                        line.addProperty("address", instruction.getAddress().toString());
                        line.addProperty("assembly", instruction.toString());
                        line.addProperty("bytes", java.util.HexFormat.of().formatHex(instruction.getBytes()));
                        decodedBytes += instruction.getLength();
                        if (instruction.getMaxAddress().compareTo(endExclusive) >= 0)
                            crossingEnd.add(instruction.getAddress().toString());
                        if (instruction.getFlowType().isJump() && instruction.getFlowType().isComputed())
                            computedJumps.add(instruction.getAddress().toString());
                        JsonArray flows = new JsonArray();
                        for (Address flow : instruction.getFlows()) flows.add(flow.toString());
                        line.add("flows", flows);
                        assembly.add(line);
                    }
                    result.add("instructions", assembly);
                    result.addProperty("disassembled_bytes_within_selected_range", decodedBytes);
                    result.add("instructions_crossing_selected_end", crossingEnd);
                    result.add("computed_jump_sites_requiring_followup", computedJumps);
                    result.addProperty("complete_control_flow_verified", false);
                    DecompileResults decoded = decompiler.decompileFunction(function, 60, monitor);
                    result.addProperty("completed", decoded.decompileCompleted());
                    result.addProperty("timed_out", decoded.isTimedOut());
                    result.addProperty("diagnostic", decoded.getErrorMessage());
                    result.addProperty("pseudocode", decoded.getDecompiledFunction() == null
                        ? "" : decoded.getDecompiledFunction().getC());
                } catch (Exception exception) {
                    result.addProperty("error", exception.toString());
                }
                Files.writeString(Path.of(args[0]), new GsonBuilder().setPrettyPrinting().create().toJson(report));
                println("FOCUSED_FUNCTION " + start + " complete=" + result.get("completed"));
            }
        } finally {
            decompiler.dispose();
        }
    }
}
