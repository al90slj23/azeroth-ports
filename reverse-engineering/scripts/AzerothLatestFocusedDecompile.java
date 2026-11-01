// Independent, bounded new-PE inspection. Does not run the imported executable.
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.ArrayList;
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
import ghidra.program.model.listing.ParameterImpl;
import ghidra.program.model.listing.Function.FunctionUpdateType;
import ghidra.program.model.data.FloatDataType;
import ghidra.program.model.data.PointerDataType;
import ghidra.program.model.data.ByteDataType;
import ghidra.program.model.data.UnsignedLongLongDataType;
import ghidra.program.model.pcode.JumpTable;
import ghidra.program.model.symbol.RefType;
import ghidra.program.model.symbol.SourceType;

public class AzerothLatestFocusedDecompile extends HeadlessScript {
    private void decode(Address start, AddressSet range) throws Exception {
        DisassembleCommand command = new DisassembleCommand(start, range, true);
        command.enableCodeAnalysis(false);
        if (!command.applyTo(currentProgram, monitor))
            println("DISASSEMBLY_STATUS " + start + " " + command.getStatusMsg());
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2) throw new IllegalArgumentException("output.json selection.json required");
        JsonArray selected = com.google.gson.JsonParser.parseString(Files.readString(Path.of(args[1]))).getAsJsonArray();
        JsonObject report = new JsonObject();
        report.addProperty("method", "project-local-ghidra-noanalysis-new-pe-selected-functions");
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
                Address end = toAddr(selection.get("end_exclusive").getAsString());
                AddressSet range = new AddressSet(start, end.subtract(1));
                if (range.getNumAddresses() > 32768) throw new IllegalArgumentException("Function exceeds 32KB");
                JsonObject result = new JsonObject();
                result.add("selection", selection.deepCopy());
                functions.add(result);
                try {
                    decode(start, range);
                    for (var seed : selection.getAsJsonArray("additional_entry_points"))
                        decode(toAddr(seed.getAsString()), range);
                    HashSet<String> resolvedSites = new HashSet<>();
                    for (var entry : selection.getAsJsonArray("verified_switches")) {
                        JsonObject verified = entry.getAsJsonObject();
                        Address site = toAddr(verified.get("site").getAsString());
                        Instruction dispatch = currentProgram.getListing().getInstructionAt(site);
                        if (dispatch == null || !dispatch.getFlowType().isComputed() || !dispatch.getFlowType().isJump())
                            throw new IllegalStateException("Validated dispatch is not a computed jump");
                        for (var target : verified.getAsJsonArray("targets")) {
                            Address destination = toAddr(target.getAsString());
                            if (!range.contains(destination) || currentProgram.getListing().getInstructionAt(destination) == null)
                                throw new IllegalStateException("Switch target lacks decoded instruction boundary");
                            dispatch.addMnemonicReference(destination, RefType.COMPUTED_JUMP, SourceType.USER_DEFINED);
                        }
                        resolvedSites.add(site.toString());
                    }
                    Function existing = currentProgram.getFunctionManager().getFunctionAt(start);
                    if (existing != null) currentProgram.getFunctionManager().removeFunction(start);
                    Function function = currentProgram.getFunctionManager().createFunction(
                        "selected_" + start.toString(), start, range, SourceType.USER_DEFINED);
                    if (selection.getAsJsonArray("verified_switches").size() != 0) {
                        // Register/type evidence: input RCX, DL, R8; SSE scalar result in XMM0.
                        // This is an analyst annotation, not a recovered Rust prototype.
                        function.setReturnType(FloatDataType.dataType, SourceType.USER_DEFINED);
                        function.replaceParameters(FunctionUpdateType.DYNAMIC_STORAGE_ALL_PARAMS, true,
                            SourceType.USER_DEFINED,
                            new ParameterImpl("state", PointerDataType.dataType, currentProgram),
                            new ParameterImpl("kind", ByteDataType.dataType, currentProgram),
                            new ParameterImpl("tier", UnsignedLongLongDataType.dataType, currentProgram));
                        result.addProperty("analyst_prototype", "float(void *state, byte kind, ulonglong tier), inferred from RCX/DL/R8/XMM0");
                        for (var entry : selection.getAsJsonArray("verified_switches")) {
                            JsonObject verified = entry.getAsJsonObject();
                            ArrayList<Address> destinations = new ArrayList<>();
                            for (var target : verified.getAsJsonArray("targets"))
                                destinations.add(toAddr(target.getAsString()));
                            // Ghidra's bundled SwitchOverride.java uses this exact API.
                            // Bound the enum switch to the five validated raw table entries.
                            new JumpTable(toAddr(verified.get("site").getAsString()), destinations, true, 0).writeOverride(function);
                        }
                    }
                    JsonArray assembly = new JsonArray();
                    JsonArray crossingEnd = new JsonArray();
                    JsonArray unresolvedJumps = new JsonArray();
                    JsonArray terminalTraps = new JsonArray();
                    JsonArray missing = new JsonArray();
                    AddressSet decoded = new AddressSet();
                    InstructionIterator instructions = currentProgram.getListing().getInstructions(range, true);
                    while (instructions.hasNext()) {
                        Instruction instruction = instructions.next();
                        JsonObject line = new JsonObject();
                        line.addProperty("address", instruction.getAddress().toString());
                        line.addProperty("assembly", instruction.toString());
                        line.addProperty("bytes", java.util.HexFormat.of().formatHex(instruction.getBytes()));
                        decoded.add(instruction.getMinAddress(), instruction.getMaxAddress());
                        if (instruction.getMaxAddress().compareTo(end) >= 0)
                            crossingEnd.add(instruction.getAddress().toString());
                        if (java.util.HexFormat.of().formatHex(instruction.getBytes()).equals("0f0b"))
                            terminalTraps.add(instruction.getAddress().toString());
                        else if (instruction.getFlowType().isJump() && instruction.getFlowType().isComputed()
                                    && !resolvedSites.contains(instruction.getAddress().toString()))
                                unresolvedJumps.add(instruction.getAddress().toString());
                        JsonArray flows = new JsonArray();
                        for (Address flow : instruction.getFlows()) flows.add(flow.toString());
                        line.add("flows", flows);
                        assembly.add(line);
                    }
                    AddressSet uncovered = range.subtract(decoded);
                    for (var gap : uncovered) {
                        JsonObject entry = new JsonObject();
                        entry.addProperty("start", gap.getMinAddress().toString());
                        entry.addProperty("end_inclusive", gap.getMaxAddress().toString());
                        missing.add(entry);
                    }
                    result.add("instructions", assembly);
                    result.addProperty("disassembled_bytes_within_selected_range", range.intersect(decoded).getNumAddresses());
                    result.addProperty("undecoded_bytes", uncovered.getNumAddresses());
                    result.add("undecoded_ranges", missing);
                    result.add("instructions_crossing_selected_end", crossingEnd);
                    result.add("unresolved_computed_jump_sites", unresolvedJumps);
                    result.add("terminal_ud2_traps", terminalTraps);
                    result.addProperty("complete_program_semantics_verified", false);
                    DecompileResults output = decompiler.decompileFunction(function, 60, monitor);
                    result.addProperty("completed", output.decompileCompleted());
                    result.addProperty("timed_out", output.isTimedOut());
                    result.addProperty("diagnostic", output.getErrorMessage());
                    result.addProperty("pseudocode", output.getDecompiledFunction() == null ? "" : output.getDecompiledFunction().getC());
                } catch (Exception exception) {
                    result.addProperty("error", exception.toString());
                }
                Files.writeString(Path.of(args[0]), new GsonBuilder().setPrettyPrinting().create().toJson(report));
                println("LATEST_FOCUSED_FUNCTION " + start + " complete=" + result.get("completed"));
            }
        } finally {
            decompiler.dispose();
        }
    }
}
